"""Generate a standard function waveform using an NI waveform generator."""

import contextlib
import logging
import pathlib
import time
from typing import Tuple

import click
import grpc
import hightime
import nifgen
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_grpc_device_channel,
    get_service_options,
    grpc_device_options,
    str_to_enum,
    use_simulation_option,
    verbosity_option,
)
from _nifgen_helpers import _create_nifgen_session

import ni_measurementlink_service as nims

# To use a physical NI waveform generator instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True

NIFGEN_OPERATION_TIMED_OUT_ERROR_CODE = -1074098044
NIFGEN_MAX_TIME_EXCEEDED_ERROR_CODE = -1074118637

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIFgenStandardFunction.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIFgenStandardFunction.measui"],
)
service_options = ServiceOptions()

WAVEFORM_TYPE_TO_ENUM = {
    "Sine": nifgen.Waveform.SINE,
    "Square": nifgen.Waveform.SQUARE,
    "Triangle": nifgen.Waveform.TRIANGLE,
    "Ramp Up": nifgen.Waveform.RAMP_UP,
    "Ramp Down": nifgen.Waveform.RAMP_DOWN,
    "DC": nifgen.Waveform.DC,
    "Noise": nifgen.Waveform.NOISE,
}


@measurement_service.register_measurement
# TODO: Rename pin_name to pin_names and make it PinArray1D
@measurement_service.configuration(
    "pin_name",
    nims.DataType.Pin,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
)
@measurement_service.configuration("waveform_type", nims.DataType.String, "Sine")
@measurement_service.configuration("frequency", nims.DataType.Double, 1.0e6)
@measurement_service.configuration("amplitude", nims.DataType.Double, 2.0)
@measurement_service.configuration("duration", nims.DataType.Double, 10.0)
def measure(
    pin_name: str,
    waveform_type: str,
    frequency: float,
    amplitude: float,
    duration: float,
) -> Tuple:
    """Generate a standard function waveform using an NI waveform generator."""
    logging.info(
        "Starting generation: pin_name=%s waveform_type=%s frequency=%g amplitude=%g",
        pin_name,
        waveform_type,
        frequency,
        amplitude,
    )

    pending_cancellation = False

    def cancel_callback():
        logging.info("Canceling generation")
        nonlocal pending_cancellation
        pending_cancellation = True

    measurement_service.context.add_cancel_callback(cancel_callback)

    session_management_client = create_session_management_client(measurement_service)

    with contextlib.ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_or_relay_names=[pin_name],
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
                # If another measurement is using the session, wait for it to complete.
                # Specify a timeout to aid in debugging missed unreserve calls.
                # Long measurements may require a longer timeout.
                timeout=60,
            )
        )

        grpc_device_channel = get_grpc_device_channel(measurement_service, nifgen)
        sessions = [
            stack.enter_context(_create_nifgen_session(session_info, grpc_device_channel))
            for session_info in reservation.session_info
        ]

        for session, session_info in zip(sessions, reservation.session_info):
            # Output mode must be the same for all channels in the session.
            session.output_mode = nifgen.OutputMode.FUNC

            channels = session.channels[session_info.channel_list]
            channels.configure_standard_waveform(
                str_to_enum(WAVEFORM_TYPE_TO_ENUM, waveform_type),
                amplitude,
                frequency,
            )

            stack.enter_context(session.initiate())

        is_simulated = sessions[0].simulate
        deadline = time.time() + measurement_service.context.time_remaining
        stop_time = time.time() + duration
        while True:
            if time.time() >= stop_time:
                break
            if time.time() > deadline:
                measurement_service.context.abort(
                    grpc.StatusCode.DEADLINE_EXCEEDED, "Deadline exceeded."
                )
            if pending_cancellation:
                measurement_service.context.abort(
                    grpc.StatusCode.CANCELLED, "Client requested cancellation."
                )
            if any((session.is_done() for session in sessions)):
                break
            remaining_time = max(stop_time - time.time(), 0.0)
            sleep_time = min(remaining_time, 100e-3)
            if is_simulated:
                time.sleep(sleep_time)
            else:
                try:
                    sessions[0].wait_until_done(hightime.timedelta(seconds=sleep_time))
                except nifgen.errors.DriverError as e:
                    """
                    There is no native way to support cancellation when generating a waveform.
                    To support cancellation, we will be calling wait_until_done
                    until it succeeds or we have gone past the specified timeout. wait_until_done
                    will throw an exception if it times out, which is why we are catching
                    and doing nothing.
                    """
                    if (
                        e.code == NIFGEN_OPERATION_TIMED_OUT_ERROR_CODE
                        or e.code == NIFGEN_MAX_TIME_EXCEEDED_ERROR_CODE
                    ):
                        pass
                    else:
                        raise

    return ()


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Generate a standard function waveform using an NI waveform generator."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

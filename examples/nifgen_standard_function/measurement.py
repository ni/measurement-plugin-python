"""Generate a standard function waveform using an NI waveform generator."""

import contextlib
import logging
import pathlib
import sys
import time
from typing import Tuple

import click
import grpc
import hightime
import nifgen
from _helpers import ServiceOptions, str_to_enum

import ni_measurementlink_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="NI-FGEN Standard Function (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NIFgenStandardFunction.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NIFgenStandardFunction_Python",
    description_url="",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)
service_options = ServiceOptions(use_grpc_device=False, grpc_device_address="")

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
@measurement_service.configuration("abort_when_done", nims.DataType.Boolean, True)
def measure(
    pin_name: str,
    waveform_type: str,
    frequency: float,
    amplitude: float,
    duration: float,
    abort_when_done: bool,
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

    session_management_client = nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )

    with contextlib.ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_or_relay_names=[pin_name],
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
                timeout=-1,
            )
        )

        sessions = [
            stack.enter_context(_create_nifgen_session(session_info))
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

            if abort_when_done:
                stack.enter_context(session.initiate())
            else:
                session.initiate()

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
                sessions[0].wait_until_done(hightime.timedelta(seconds=sleep_time))

    return ()


def _create_nifgen_session(
    session_info: nims.session_management.SessionInformation,
) -> nifgen.Session:
    session_kwargs = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=nifgen.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        # Assumption: the pin map specifies one NI-FGEN session per instrument. If the pin map
        # specified an NI-FGEN session per channel, the session name would need to include the
        # channel name(s).
        session_kwargs["grpc_options"] = nifgen.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=nifgen.SessionInitializationBehavior.AUTO,
        )

    return nifgen.Session(session_info.resource_name, session_info.channel_list, **session_kwargs)


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
@click.option(
    "--use-grpc-device/--no-use-grpc-device",
    default=True,
    is_flag=True,
    help="Use the NI gRPC Device Server.",
)
@click.option(
    "--grpc-device-address",
    default="",
    help="NI gRPC Device Server address (e.g. localhost:31763). If unspecified, use the discovery service to resolve the address.",
)
def main(verbose: int, use_grpc_device: bool, grpc_device_address: str):
    """Generate a standard function waveform using an NI waveform generator."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    global service_options
    service_options = ServiceOptions(
        use_grpc_device=use_grpc_device, grpc_device_address=grpc_device_address
    )

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    sys.exit(main())

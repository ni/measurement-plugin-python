"""Generate a standard function waveform using an NI waveform generator."""

import logging
import pathlib
import sys
import threading
import time
from collections.abc import Iterable, Sequence
from contextlib import ExitStack
from enum import Enum

import click
import grpc
import hightime
import ni_measurement_plugin_sdk_service as nims
import nifgen
from _helpers import configure_logging, verbosity_option

_NIFGEN_OPERATION_TIMED_OUT_ERROR_CODE = -1074098044
_NIFGEN_MAX_TIME_EXCEEDED_ERROR_CODE = -1074118637
_NIFGEN_TIMEOUT_ERROR_CODES = [
    _NIFGEN_OPERATION_TIMED_OUT_ERROR_CODE,
    _NIFGEN_MAX_TIME_EXCEEDED_ERROR_CODE,
]

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIFgenStandardFunction.serviceconfig",
    ui_file_paths=[service_directory / "NIFgenStandardFunction.measui"],
)


class Waveform(Enum):
    """Wrapper enum that contains a zero value."""

    NONE = 0
    SINE = nifgen.Waveform.SINE.value
    SQUARE = nifgen.Waveform.SQUARE.value
    TRIANGLE = nifgen.Waveform.TRIANGLE.value
    RAMP_UP = nifgen.Waveform.RAMP_UP.value
    RAMP_DOWN = nifgen.Waveform.RAMP_DOWN.value
    DC = nifgen.Waveform.DC.value
    NOISE = nifgen.Waveform.NOISE.value
    USER = nifgen.Waveform.USER.value


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.IOResourceArray1D,
    ["Pin1"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
)
@measurement_service.configuration(
    "waveform_type", nims.DataType.Enum, Waveform.SINE, enum_type=Waveform
)
@measurement_service.configuration("frequency", nims.DataType.Double, 1.0e6)
@measurement_service.configuration("amplitude", nims.DataType.Double, 2.0)
@measurement_service.configuration("duration", nims.DataType.Double, 10.0)
def measure(
    pin_names: Iterable[str],
    waveform_type: Waveform,
    frequency: float,
    amplitude: float,
    duration: float,
) -> tuple[()]:
    """Generate a standard function waveform using an NI waveform generator."""
    logging.info(
        "Starting generation: pin_names=%s waveform_type=%s frequency=%g amplitude=%g",
        pin_names,
        waveform_type,
        frequency,
        amplitude,
    )

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    # If the waveform type is not specified, use SINE.
    nifgen_waveform = nifgen.Waveform(waveform_type.value or Waveform.SINE.value)

    with measurement_service.context.reserve_sessions(pin_names) as reservation:
        with reservation.initialize_nifgen_sessions() as session_infos:
            for session_info in session_infos:
                # Output mode must be the same for all channels in the session.
                session_info.session.output_mode = nifgen.OutputMode.FUNC

                # Configure the same waveform settings for all channels
                # corresponding to the selected pins and sites.
                channels = session_info.session.channels[session_info.channel_list]
                channels.configure_standard_waveform(nifgen_waveform, amplitude, frequency)

            with ExitStack() as stack:
                # Initiate the generation for all sessions. initiate() returns a
                # context manager that aborts the generation when the function
                # returns or raises an exception. Use an ExitStack to manage
                # multiple context managers.
                for session_info in session_infos:
                    stack.enter_context(session_info.session.initiate())

                # Wait until the generation is done.
                sessions = [session_info.session for session_info in session_infos]
                _wait_until_done(sessions, cancellation_event, duration)

    logging.info("Completed generation")
    return ()


def _wait_until_done(
    sessions: Sequence[nifgen.Session], cancellation_event: threading.Event, duration: float
) -> None:
    """Wait until all sessions are done, the duration expires, or error/cancellation occurs.

    Note that ``duration`` is a minimum time, not a timeout.
    """
    is_simulated = any(session.simulate for session in sessions)
    grpc_deadline = time.time() + measurement_service.context.time_remaining
    stop_time = time.time() + duration

    while True:
        if time.time() >= stop_time:
            break
        if time.time() > grpc_deadline:
            measurement_service.context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED, "Deadline exceeded."
            )
        if cancellation_event.is_set():
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

        if is_simulated:
            # With simulated NI-FGEN instruments, wait_for_done() succeeds
            # immediately, so use time.sleep() instead.
            remaining_time = max(stop_time - time.time(), 0.0)
            sleep_time = min(remaining_time, 100e-3)
            time.sleep(sleep_time)
        else:
            # Wait until all sessions are done. If any session takes more than
            # 100 ms, check for cancellation and try again. NI-FGEN does not
            # support canceling a call to wait_until_done().
            try:
                for session in sessions:
                    remaining_time = max(stop_time - time.time(), 0.0)
                    sleep_time = min(remaining_time, 100e-3)
                    session.wait_until_done(hightime.timedelta(seconds=sleep_time))
                break
            except nifgen.errors.DriverError as e:
                if e.code in _NIFGEN_TIMEOUT_ERROR_CODES:
                    pass
                raise


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Generate a standard function waveform using an NI waveform generator."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

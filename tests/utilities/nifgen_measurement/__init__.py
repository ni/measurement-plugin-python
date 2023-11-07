"""NI-Fgen MeasurementLink test service."""
import pathlib
import time
from contextlib import ExitStack
from typing import Iterable, Sequence, Tuple

import hightime
import nifgen

import ni_measurementlink_service as nims
from ni_measurementlink_service.session_management import TypedSessionInformation

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIFgenMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.PinArray1D, ["Pin1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
def measure(
    pin_names: Iterable[str], multi_session: bool
) -> Tuple[Iterable[str], Iterable[str], Iterable[str], Iterable[str]]:
    """NI-Fgen MeasurementLink test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nifgen_sessions() as session_infos:
                assert all([session_info.session is not None for session_info in session_infos])
                connections = reservation.get_nifgen_connections(pin_names)
                _generate_standard_waveform(session_infos)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nifgen_session() as session_info:
                assert session_info.session is not None
                connection = reservation.get_nifgen_connection(list(pin_names)[0])
                _generate_standard_waveform([session_info])

                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                )


def _generate_standard_waveform(
    session_infos: Sequence[TypedSessionInformation[nifgen.Session]],
) -> None:
    for session_info in session_infos:
        session_info.session.output_mode = nifgen.OutputMode.FUNC
        channels = session_info.session.channels[session_info.channel_list]
        channels.configure_standard_waveform(nifgen.Waveform.SINE, 2.0, 1.0e6)

    with ExitStack() as stack:
        for session_info in session_infos:
            stack.enter_context(session_info.session.initiate())

    sessions = [session_info.session for session_info in session_infos]
    is_simulated = any(session.simulate for session in sessions)

    if is_simulated:
        time.sleep(100e-3)
    else:
        try:
            stop_time = time.time() + 10
            for session in sessions:
                remaining_time = max(stop_time - time.time(), 0.0)
                sleep_time = min(remaining_time, 100e-3)
                session.wait_until_done(hightime.timedelta(seconds=sleep_time))
        except nifgen.errors.DriverError as e:
            if e.code in [-1074098044, -1074118637]:
                pass
            raise

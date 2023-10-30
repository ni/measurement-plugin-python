"""NI-DCPower MeasurementLink test service."""
import pathlib
from typing import Iterable, Tuple

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDCPowerMeasurement.serviceconfig",
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
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> Tuple[Iterable[str], Iterable[str], Iterable[str]]:
    """NI-DCPower MeasurementLink test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nidcpower_sessions() as session_infos:
                assert [session_info.session is not None for session_info in session_infos]
                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nidcpower_session() as session_info:
                assert session_info.session is not None
                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                )

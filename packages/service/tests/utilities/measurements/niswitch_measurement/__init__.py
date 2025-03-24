"""NI-SWITCH measurement plug-in test service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Sequence
from typing import Tuple

import niswitch

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service.session_management import TypedSessionInformation

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NISwitchMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("relay_names", nims.DataType.StringArray1D, ["SiteRelay1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
def measure(
    relay_names: Iterable[str],
    multi_session: bool,
) -> tuple[Iterable[str], Iterable[str], Iterable[str], Iterable[str]]:
    """NI-SWITCH measurement plug-in test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(relay_names) as reservation:
            with reservation.initialize_niswitch_sessions() as session_infos:
                connections = reservation.get_niswitch_connections(relay_names)
                assert all([session_info.session is not None for session_info in session_infos])
                _control_relays(session_infos)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                )
    else:
        with measurement_service.context.reserve_session(relay_names) as reservation:
            with reservation.initialize_niswitch_session() as session_info:
                connection = reservation.get_niswitch_connection(list(relay_names)[0])
                assert session_info.session is not None
                _control_relays([session_info])

                return (
                    [session_info.session_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                )


def _control_relays(
    session_infos: Sequence[TypedSessionInformation[niswitch.Session]],
) -> None:
    for session_info in session_infos:
        session_info.session.relay_control(
            session_info.channel_list, niswitch.enums.RelayAction.CLOSE
        )

    for session_info in session_infos:
        session_info.session.wait_for_debounce()

"""NI-SWITCH multiplexer measurement plug-in test service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Sequence
from typing import Tuple

import niswitch

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service.session_management import (
    TypedConnectionWithMultiplexer,
)

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NISwitchMultiplexerMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.IOResourceArray1D, ["Pin1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("multiplexer_session_names", nims.DataType.StringArray1D)
@measurement_service.output("multiplexer_resource_names", nims.DataType.StringArray1D)
@measurement_service.output("multiplexer_routes", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> tuple[Iterable[str], Iterable[str], Iterable[str], Iterable[str]]:
    """NI-SWITCH multiplexer measurement plug-in test service."""
    if multi_session:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_niswitch_multiplexer_sessions() as multiplexer_session_infos:
                connections = reservation.get_connections_with_multiplexer(
                    object, niswitch.Session, pin_names
                )
                assert all(
                    [session_info.session is not None for session_info in multiplexer_session_infos]
                )
                _control_relays(connections)

                return (
                    [session_info.session_name for session_info in multiplexer_session_infos],
                    [session_info.resource_name for session_info in multiplexer_session_infos],
                    [connection.multiplexer_route for connection in connections],
                    [connection.channel_name for connection in connections],
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_niswitch_multiplexer_session() as multiplexer_session_info:
                connection = reservation.get_connection_with_multiplexer(
                    object, niswitch.Session, list(pin_names)[0]
                )
                assert multiplexer_session_info.session is not None
                _control_relays([connection])

                return (
                    [multiplexer_session_info.resource_name],
                    [multiplexer_session_info.resource_name],
                    [connection.multiplexer_route],
                    [connection.channel_name],
                )


def _control_relays(
    connections: Sequence[TypedConnectionWithMultiplexer],
) -> None:
    for connection in connections:
        connection.multiplexer_session.connect_multiple(connection.multiplexer_route)

    for connection in connections:
        connection.multiplexer_session.wait_for_debounce()

    for connection in connections:
        connection.multiplexer_session.disconnect_multiple(connection.multiplexer_route)

    for connection in connections:
        connection.multiplexer_session.wait_for_debounce()

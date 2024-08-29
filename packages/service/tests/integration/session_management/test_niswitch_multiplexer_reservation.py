import pathlib
from contextlib import ExitStack

import niswitch
import pytest

from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import (
    PinMapContext,
    SessionManagementClient,
)
from tests.utilities.connection_subset import (
    ConnectionSubset,
    get_connection_subset_with_multiplexer,
)

_SITE = 0


def test___reserved_single_session_with_single_multiplexer___initialize_niswitch_multiplexer_session___creates_single_multiplexer_session(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )

        multiplexer_session_info = stack.enter_context(
            reservation.initialize_niswitch_multiplexer_session()
        )

        assert multiplexer_session_info.session is not None
        assert multiplexer_session_info.session_name == "Multiplexer2"


def test___reserved_sessions_with_multiple_multiplexer___initialize_niswitch_multiplexer_sessions___creates_multiple_multiplexer_sessions(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1", "Pin2"]
    niswitch_multiplexer_resources = ["Multiplexer1", "Multiplexer2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_names)
        )

        multiplexer_session_infos = stack.enter_context(
            reservation.initialize_niswitch_multiplexer_sessions()
        )

        assert all([session_info.session is not None for session_info in multiplexer_session_infos])
        assert [
            session_info.session_name == expected_resource
            for session_info, expected_resource in zip(
                multiplexer_session_infos, niswitch_multiplexer_resources
            )
        ]


def test___created_single_session___get_nidcpower_connection_with_multiplexer___returns_connection_with_multiplexer_session(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_nidcpower_session())
        stack.enter_context(reservation.initialize_niswitch_multiplexer_session())

        connection = reservation.get_nidcpower_connection_with_multiplexer(
            niswitch.Session, pin_names[0]
        )

        assert connection.multiplexer_session is not None
        assert get_connection_subset_with_multiplexer(connection) == ConnectionSubset(
            pin_names[0],
            _SITE,
            "DCPower1/0, DCPower1/1",
            "DCPower1/0",
            "Multiplexer2",
            "C1->r2, C2->r2",
        )


def test___created_multiple_sessions___get_nidcpower_connections_with_multiplexer___returns_connections_with_multiplexer_sessions(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1", "Pin2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_nidcpower_sessions())
        stack.enter_context(reservation.initialize_niswitch_multiplexer_sessions())

        connections = reservation.get_nidcpower_connections_with_multiplexer(
            niswitch.Session, pin_names
        )

        assert all([conn.multiplexer_session is not None for conn in connections])
        assert [
            get_connection_subset_with_multiplexer(connection) for connection in connections
        ] == [
            ConnectionSubset(
                pin_names[0],
                _SITE,
                "DCPower1/0, DCPower1/1",
                "DCPower1/0",
                "Multiplexer2",
                "C1->r2, C2->r2",
            ),
            ConnectionSubset(
                pin_names[1],
                _SITE,
                "DCPower1/0, DCPower1/1",
                "DCPower1/1",
                "Multiplexer1",
                "C3->r1, C4->r1",
            ),
        ]


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "1Smu2Multiplexer2Pin1Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

    return PinMapContext(pin_map_id=pin_map_id, sites=[_SITE])

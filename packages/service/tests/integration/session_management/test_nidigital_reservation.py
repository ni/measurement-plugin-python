import pathlib
from contextlib import ExitStack

import pytest

from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import (
    PinMapContext,
    SessionManagementClient,
)
from tests.utilities.connection_subset import ConnectionSubset, get_connection_subset


def test___single_session_reserved___initialize_nidigital_session___creates_single_session(
    pin_map_id: str,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["CS"]
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )

        session_info = stack.enter_context(reservation.initialize_nidigital_session())

        assert session_info.session is not None
        assert session_info.session_name == "DigitalPattern1"


def test___multiple_sessions_reserved___initialize_nidigital_sessions___creates_multiple_sessions(
    pin_map_id: str,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["CS", "SCLK"]
    nidigital_resource = ["DigitalPattern1", "DigitalPattern2"]
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_names)
        )

        session_infos = stack.enter_context(reservation.initialize_nidigital_sessions())

        assert all([session_info.session is not None for session_info in session_infos])
        assert [
            session_info.session_name == expected_resouce
            for session_info, expected_resouce in zip(session_infos, nidigital_resource)
        ]


def test___session_created___get_nidigital_connection___returns_connection(
    pin_map_id: str,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["CS"]
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_nidigital_session())

        connection = reservation.get_nidigital_connection(pin_names[0])

        assert get_connection_subset(connection) == ConnectionSubset(
            pin_names[0], 0, "DigitalPattern1", "site0/CS"
        )


def test___session_created___get_nidigital_connections___returns_connections(
    pin_map_id: str,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["CS", "SCLK"]
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_nidigital_session())

        connections = reservation.get_nidigital_connections(pin_names)

        assert [get_connection_subset(connection) for connection in connections] == [
            ConnectionSubset(pin_names[0], 0, "DigitalPattern1", "site0/CS"),
            ConnectionSubset(pin_names[1], 0, "DigitalPattern1", "site0/SCLK"),
        ]


@pytest.fixture
def pin_map_id(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> str:
    pin_map_name = "2Digital2Group4Pin1Site.pinmap"
    return pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

import pathlib
from contextlib import ExitStack

import pytest
from ni.measurementlink.pinmap.v1.client import PinMapClient
from ni.measurementlink.sessionmanagement.v1.client import (
    PinMapContext,
    SessionManagementClient,
)

from tests.utilities.connection_subset import ConnectionSubset, get_connection_subset

_SITE = 0


def test___single_session_reserved___initialize_niscope_session___creates_single_session(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )

        session_info = stack.enter_context(reservation.initialize_niscope_session())

        assert session_info.session is not None
        assert session_info.session_name == "SCOPE1" or session_info.session_name == "niScope-SCOPE1"


def test___multiple_sessions_reserved___initialize_niscope_sessions___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1", "Pin2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_names)
        )

        session_infos = stack.enter_context(reservation.initialize_niscope_sessions())

        assert all([session_info.session is not None for session_info in session_infos])
        assert session_infos[0].session_name == "SCOPE1" or session_infos[0].session_name == "niScope-SCOPE1"
        assert session_infos[1].session_name == "SCOPE2" or session_infos[1].session_name == "niScope-SCOPE2"


def test___session_created___get_niscope_connection___returns_connection(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_niscope_session())

        connection = reservation.get_niscope_connection(pin_names[0])

        assert get_connection_subset(connection) == ConnectionSubset(
            pin_names[0], _SITE, "SCOPE1", "0"
        )


def test___sessions_created___get_niscope_connections___returns_connections(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    pin_names = ["Pin1", "Pin2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_names)
        )
        stack.enter_context(reservation.initialize_niscope_sessions())

        connections = reservation.get_niscope_connections(pin_names)

        assert [get_connection_subset(connection) for connection in connections] == [
            ConnectionSubset(pin_names[0], _SITE, "SCOPE1", "0"),
            ConnectionSubset(pin_names[1], _SITE, "SCOPE2", "0"),
        ]


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "2Scope2Pin2Group1Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

    return PinMapContext(pin_map_id=pin_map_id, sites=[_SITE])

import pathlib
from contextlib import ExitStack

import pytest

from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import (
    PinMapContext,
    SessionManagementClient,
)
from tests.utilities.connection_subset import ConnectionSubset, get_connection_subset

_SITE = 0


def test___single_session_reserved___initialize_niswitch_session___creates_single_session(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    relay_names = ["SiteRelay1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, relay_names)
        )

        session_info = stack.enter_context(reservation.initialize_niswitch_session())

        assert session_info.session is not None
        assert session_info.session_name == "RelayDriver1"


def test___multiple_sessions_reserved___initialize_niswitch_sessions___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    relay_names = ["SiteRelay1", "SiteRelay2"]
    niswitch_resource = ["RelayDriver1", "RelayDriver2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, relay_names)
        )

        session_infos = stack.enter_context(reservation.initialize_niswitch_sessions())

        assert all([session_info.session is not None for session_info in session_infos])
        assert [
            session_info.session_name == expected_resource
            for session_info, expected_resource in zip(session_infos, niswitch_resource)
        ]


def test___session_created___get_niswitch_connection___returns_connection(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    relay_names = ["SiteRelay1"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_session(pin_map_context, relay_names)
        )
        stack.enter_context(reservation.initialize_niswitch_session())

        connection = reservation.get_niswitch_connection(relay_names[0])

        assert get_connection_subset(connection) == ConnectionSubset(
            relay_names[0], _SITE, "RelayDriver1", "K0"
        )


def test___sessions_created___get_niswitch_connections___returns_connections(
    pin_map_context: PinMapContext,
    session_management_client: SessionManagementClient,
) -> None:
    relay_names = ["SiteRelay1", "SiteRelay2"]
    with ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, relay_names)
        )
        stack.enter_context(reservation.initialize_niswitch_sessions())

        connections = reservation.get_niswitch_connections(relay_names)

        assert [get_connection_subset(connection) for connection in connections] == [
            ConnectionSubset(relay_names[0], _SITE, "RelayDriver1", "K0"),
            ConnectionSubset(relay_names[1], _SITE, "RelayDriver2", "K1"),
        ]


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "2Switch2Relay1Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

    return PinMapContext(pin_map_id=pin_map_id, sites=[_SITE])

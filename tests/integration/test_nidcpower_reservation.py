import pathlib
from typing import NamedTuple, TypeVar, Union

import pytest

from ni_measurementlink_service.session_management import (
    Connection,
    PinMapContext,
    SessionManagementClient,
    TypedConnection,
)
from tests.utilities.pin_map_client import PinMapClient


def test___single_session_reserved___initialize_nidcpower_session___single_session_created(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    pin_map_name = "1Smu2ChannelGroup2Pin1Site.pinmap"
    pin_names = ["Pin1"]
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with session_management_client.reserve_session(
        pin_map_context, pin_names, timeout=0
    ) as reservation:
        with reservation.initialize_nidcpower_session() as session_info:
            assert session_info.session is not None

        assert session_info.session_name == "DCPower1/0"


def test___multiple_sessions_reserved___initialize_nidcpower_sessions___multiple_sessions_created(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    pin_map_name = "1Smu2ChannelGroup2Pin1Site.pinmap"
    pin_names = ["Pin1", "Pin2"]
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with session_management_client.reserve_sessions(
        pin_map_context, pin_names, timeout=0
    ) as reservation:
        with reservation.initialize_nidcpower_sessions() as session_infos:
            assert [session_info.session is not None for session_info in session_infos]

        assert session_infos[0].session_name == "DCPower1/0"
        assert session_infos[1].session_name == "DCPower1/2"


def test___session_created___get_nidcpower_connection___connection_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    pin_map_name = "1Smu2ChannelGroup2Pin1Site.pinmap"
    pin_name = "Pin1"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with session_management_client.reserve_session(
        pin_map_context, pin_name, timeout=0
    ) as reservation:
        with reservation.initialize_nidcpower_session():
            connection = reservation.get_nidcpower_connection(pin_name)

            assert _get_subset(connection) == _ConnectionSubset(
                pin_name, 0, "DCPower1/0", "DCPower1/0"
            )


def test___sessions_created___get_nidcpower_connections___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    pin_map_name = "1Smu2ChannelGroup2Pin1Site.pinmap"
    pin_names = ["Pin1", "Pin2"]
    site = 0
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[site])
    with session_management_client.reserve_sessions(
        pin_map_context, pin_names, timeout=0
    ) as reservation:
        with reservation.initialize_nidcpower_sessions():
            connections = reservation.get_nidcpower_connections(pin_names)

            assert [_get_subset(connection) for connection in connections] == [
                _ConnectionSubset(pin_names[0], site, "DCPower1/0", "DCPower1/0"),
                _ConnectionSubset(pin_names[1], site, "DCPower1/2", "DCPower1/2"),
            ]


@pytest.fixture
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "integration" / "session_management"


_T = TypeVar("_T")


class _ConnectionSubset(NamedTuple):
    pin_or_relay_name: str
    site: int

    resource_name: str
    channel_name: str


def _get_subset(connection: Union[Connection, TypedConnection[_T]]) -> _ConnectionSubset:
    return _ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.session_info.resource_name,
        connection.channel_name,
    )

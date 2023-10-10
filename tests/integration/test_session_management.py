from __future__ import annotations

import pathlib
from contextlib import ExitStack
from typing import NamedTuple, TypeVar, Union

import pytest

from ni_measurementlink_service.session_management import (
    Connection,
    PinMapContext,
    SessionManagementClient,
    TypedConnection,
)
from tests.utilities.pin_map_client import PinMapClient

_PIN_MAP_A = "MultisitePinMapA-3Instruments_3DutPins_2SystemPins_2Sites.pinmap"


def test___pin_map_a_reserved___get_connections___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["A", "B", "C", "S1", "S2"])
        )

        connections = reservation.get_connections(object)

        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("A", 0, "DCPower1/0", "niDCPower"),
            _ConnectionSubset("B", 0, "DCPower1/2", "niDCPower"),
            _ConnectionSubset("C", 0, "0", "niScope"),
            _ConnectionSubset("A", 1, "DCPower1/1", "niDCPower"),
            _ConnectionSubset("B", 1, "DCPower2/1", "niDCPower"),
            _ConnectionSubset("C", 1, "1", "niScope"),
            _ConnectionSubset("S1", -1, "DCPower1/3", "niDCPower"),
            _ConnectionSubset("S2", -1, "3", "niScope"),
        ]


def test___pin_map_a_reserved___get_connections_by_pin___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["A", "B", "C", "S1", "S2"])
        )

        connections = [
            reservation.get_connections(object, pin_name)
            for pin_name in ["A", "B", "C", "S1", "S2"]
        ]

        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, "DCPower1/0", "niDCPower"),
                _ConnectionSubset("A", 1, "DCPower1/1", "niDCPower"),
            ],
            [
                _ConnectionSubset("B", 0, "DCPower1/2", "niDCPower"),
                _ConnectionSubset("B", 1, "DCPower2/1", "niDCPower"),
            ],
            [
                _ConnectionSubset("C", 0, "0", "niScope"),
                _ConnectionSubset("C", 1, "1", "niScope"),
            ],
            [
                _ConnectionSubset("S1", -1, "DCPower1/3", "niDCPower"),
            ],
            [
                _ConnectionSubset("S2", -1, "3", "niScope"),
            ],
        ]


def test___pin_map_a_reserved___get_connections_by_site___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["A", "B", "C", "S1", "S2"])
        )

        connections = [reservation.get_connections(object, sites=site) for site in [0, 1]]

        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, "DCPower1/0", "niDCPower"),
                _ConnectionSubset("B", 0, "DCPower1/2", "niDCPower"),
                _ConnectionSubset("C", 0, "0", "niScope"),
                _ConnectionSubset("S1", -1, "DCPower1/3", "niDCPower"),
                _ConnectionSubset("S2", -1, "3", "niScope"),
            ],
            [
                _ConnectionSubset("A", 1, "DCPower1/1", "niDCPower"),
                _ConnectionSubset("B", 1, "DCPower2/1", "niDCPower"),
                _ConnectionSubset("C", 1, "1", "niScope"),
                _ConnectionSubset("S1", -1, "DCPower1/3", "niDCPower"),
                _ConnectionSubset("S2", -1, "3", "niScope"),
            ],
        ]


def test___pin_map_a_reserved___get_connections_by_instrument_type___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["A", "B", "C", "S1", "S2"])
        )

        connections = [
            reservation.get_connections(object, instrument_type_id=instrument_type_id)
            for instrument_type_id in ["niDCPower", "niScope"]
        ]

        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, "DCPower1/0", "niDCPower"),
                _ConnectionSubset("B", 0, "DCPower1/2", "niDCPower"),
                _ConnectionSubset("A", 1, "DCPower1/1", "niDCPower"),
                _ConnectionSubset("B", 1, "DCPower2/1", "niDCPower"),
                _ConnectionSubset("S1", -1, "DCPower1/3", "niDCPower"),
            ],
            [
                _ConnectionSubset("C", 0, "0", "niScope"),
                _ConnectionSubset("C", 1, "1", "niScope"),
                _ConnectionSubset("S2", -1, "3", "niScope"),
            ],
        ]


@pytest.fixture
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "integration" / "session_management"


_T = TypeVar("_T")


class _ConnectionSubset(NamedTuple):
    pin_or_relay_name: str
    site: int
    channel_name: str
    instrument_type_id: str


def _get_subset(connection: Union[Connection, TypedConnection[_T]]) -> _ConnectionSubset:
    return _ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.channel_name,
        connection.session_info.instrument_type_id,
    )

from __future__ import annotations

import pathlib
from contextlib import ExitStack

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DCPOWER,
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    INSTRUMENT_TYPE_NI_SCOPE,
    PinMapContext,
    SessionManagementClient,
)
from tests.integration._reservation_utils import _ConnectionSubset, _get_subset
from tests.utilities.pin_map_client import PinMapClient

_PIN_MAP_A = "PinMapA_3Instruments_3DutPins_2SystemPins_2Sites.pinmap"
_PIN_MAP_A_PIN_NAMES = ["A", "B", "C", "S1", "S2"]

_PIN_MAP_B = "PinMapB_3Instruments_3DutPins_2SystemPins_2Sites_SharedPins.pinmap"
_PIN_MAP_B_PIN_NAMES = ["A", "B", "C", "S1", "S2"]

_PIN_MAP_C = "PinMapC_MultipleInstrumentsPinsRelaysAndSites.pinmap"
_PIN_MAP_C_PIN_NAMES = ["A", "B", "C", "S1", "S2"]
_PIN_MAP_C_RELAY_NAMES = ["RelayUsingDifferentDrivers", "RelayUsingSameDriver", "SystemRelay"]
_PIN_MAP_C_PIN_OR_RELAY_NAMES = _PIN_MAP_C_PIN_NAMES + _PIN_MAP_C_RELAY_NAMES


def test___sessions_reserved___get_connections___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_A_PIN_NAMES)
        )

        connections = reservation.get_connections(object)

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3, DCPower2/1"
        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            _ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
            _ConnectionSubset("C", 0, "SCOPE1", "0"),
            _ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
            _ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            _ConnectionSubset("C", 1, "SCOPE1", "1"),
            _ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            _ConnectionSubset("S2", -1, "SCOPE1", "3"),
        ]


def test___sessions_reserved___get_connections_by_pin___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_A_PIN_NAMES)
        )

        connections = [
            reservation.get_connections(object, pin_name) for pin_name in _PIN_MAP_A_PIN_NAMES
        ]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3, DCPower2/1"
        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                _ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
            ],
            [
                _ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                _ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            ],
            [
                _ConnectionSubset("C", 0, "SCOPE1", "0"),
                _ConnectionSubset("C", 1, "SCOPE1", "1"),
            ],
            [
                _ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            ],
            [
                _ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
        ]


def test___sessions_reserved___get_connections_by_site___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_A_PIN_NAMES)
        )

        connections = [reservation.get_connections(object, sites=site) for site in [0, 1]]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3, DCPower2/1"
        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                _ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                _ConnectionSubset("C", 0, "SCOPE1", "0"),
                _ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
                _ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
            [
                _ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
                _ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
                _ConnectionSubset("C", 1, "SCOPE1", "1"),
                _ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
                _ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
        ]


def test___sessions_reserved___get_connections_by_instrument_type___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_A)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_A_PIN_NAMES)
        )

        connections = [
            reservation.get_connections(object, instrument_type_id=instrument_type_id)
            for instrument_type_id in [INSTRUMENT_TYPE_NI_DCPOWER, INSTRUMENT_TYPE_NI_SCOPE]
        ]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3, DCPower2/1"
        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                _ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                _ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
                _ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
                _ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            ],
            [
                _ConnectionSubset("C", 0, "SCOPE1", "0"),
                _ConnectionSubset("C", 1, "SCOPE1", "1"),
                _ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
        ]


# AB#2546523: Fully support querying connections for shared pins
#
# When you reserve sessions for all sites, the session management service
# currently only returns shared pins for the 1st site with which they are
# associated.
def test___sessions_reserved_with_shared_pins_all_sites___get_connections___connections_returned_for_first_matching_site(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_B)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_B_PIN_NAMES)
        )

        connections = reservation.get_connections(object)

        nidcpower_resource = "DCPower1/0, DCPower1/2, DCPower2/1"
        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            _ConnectionSubset("B", 0, nidcpower_resource, "DCPower2/1"),
            _ConnectionSubset("C", 0, "SCOPE1", "2"),
            _ConnectionSubset("S1", -1, "SCOPE1", "1"),
            _ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
        ]


def test___sessions_reserved_with_shared_pins_site0___get_connections___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_B)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_B_PIN_NAMES)
        )

        connections = reservation.get_connections(object)

        nidcpower_resource = "DCPower1/0, DCPower1/2, DCPower2/1"
        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            _ConnectionSubset("B", 0, nidcpower_resource, "DCPower2/1"),
            _ConnectionSubset("C", 0, "SCOPE1", "2"),
            _ConnectionSubset("S1", -1, "SCOPE1", "1"),
            _ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
        ]


def test___sessions_reserved_with_shared_pins_site1___get_connections___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_B)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_B_PIN_NAMES)
        )

        connections = reservation.get_connections(object)

        nidcpower_resource = "DCPower1/0, DCPower1/2, DCPower2/1"
        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/0"),
            _ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            _ConnectionSubset("C", 1, "SCOPE1", "2"),
            _ConnectionSubset("S1", -1, "SCOPE1", "1"),
            _ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
        ]


def test___sessions_reserved_with_relays___get_connections_for_relay_driver___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                pin_map_context, _PIN_MAP_C_PIN_OR_RELAY_NAMES
            )
        )

        connections = reservation.get_connections(
            object, instrument_type_id=INSTRUMENT_TYPE_NI_RELAY_DRIVER
        )

        assert [_get_subset(conn) for conn in connections] == [
            _ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
            _ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            _ConnectionSubset("RelayUsingDifferentDrivers", 1, "RelayDriver2", "K10"),
            _ConnectionSubset("RelayUsingSameDriver", 1, "RelayDriver1", "K1"),
            _ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
        ]


def test___sessions_reserved_with_relays___get_connections_for_relay_driver_by_site___connections_returned(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                pin_map_context, _PIN_MAP_C_PIN_OR_RELAY_NAMES
            )
        )

        connections = [
            reservation.get_connections(
                object, sites=site, instrument_type_id=INSTRUMENT_TYPE_NI_RELAY_DRIVER
            )
            for site in [0, 1]
        ]

        assert [[_get_subset(conn) for conn in group] for group in connections] == [
            [
                _ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
                _ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
                _ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
            ],
            [
                _ConnectionSubset("RelayUsingDifferentDrivers", 1, "RelayDriver2", "K10"),
                _ConnectionSubset("RelayUsingSameDriver", 1, "RelayDriver1", "K1"),
                _ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
            ],
        ]

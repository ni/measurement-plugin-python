from __future__ import annotations

import pathlib
from contextlib import ExitStack

from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import (
    INSTRUMENT_TYPE_NI_DCPOWER,
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    INSTRUMENT_TYPE_NI_SCOPE,
    PinMapContext,
    SessionManagementClient,
)
from tests.utilities.connection_subset import (
    ConnectionSubset,
    get_connection_subset,
    get_connection_subset_with_multiplexer,
)

_PIN_MAP_A = "PinMapA_3Instruments_3DutPins_2SystemPins_2Sites.pinmap"
_PIN_MAP_A_PIN_NAMES = ["A", "B", "C", "S1", "S2"]

_PIN_MAP_B = "PinMapB_3Instruments_3DutPins_2SystemPins_2Sites_SharedPins.pinmap"
_PIN_MAP_B_PIN_NAMES = ["A", "B", "C", "S1", "S2"]

_PIN_MAP_C = "PinMapC_MultipleInstrumentsPinsRelaysAndSites.pinmap"
_PIN_MAP_C_PIN_NAMES = ["A", "B", "C", "S1", "S2"]
_PIN_MAP_C_RELAY_NAMES = ["RelayUsingDifferentDrivers", "RelayUsingSameDriver", "SystemRelay"]
_PIN_MAP_C_PIN_OR_RELAY_NAMES = _PIN_MAP_C_PIN_NAMES + _PIN_MAP_C_RELAY_NAMES

_PIN_MAP_D = "PinMapD_3Instruments_4DutPins_2Sites_2Multiplexers.pinmap"
_PIN_MAP_D_PIN_NAMES = ["A", "B", "C", "D"]


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
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
            ConnectionSubset("C", 0, "SCOPE1", "0"),
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
            ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            ConnectionSubset("C", 1, "SCOPE1", "1"),
            ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            ConnectionSubset("S2", -1, "SCOPE1", "3"),
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
        assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
            [
                ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
            ],
            [
                ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            ],
            [
                ConnectionSubset("C", 0, "SCOPE1", "0"),
                ConnectionSubset("C", 1, "SCOPE1", "1"),
            ],
            [
                ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            ],
            [
                ConnectionSubset("S2", -1, "SCOPE1", "3"),
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
        assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
            [
                ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                ConnectionSubset("C", 0, "SCOPE1", "0"),
                ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
                ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
            [
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
                ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
                ConnectionSubset("C", 1, "SCOPE1", "1"),
                ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
                ConnectionSubset("S2", -1, "SCOPE1", "3"),
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
        assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
            [
                ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
                ConnectionSubset("B", 0, nidcpower_resource, "DCPower1/2"),
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1"),
                ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
                ConnectionSubset("S1", -1, nidcpower_resource, "DCPower1/3"),
            ],
            [
                ConnectionSubset("C", 0, "SCOPE1", "0"),
                ConnectionSubset("C", 1, "SCOPE1", "1"),
                ConnectionSubset("S2", -1, "SCOPE1", "3"),
            ],
        ]


def test___sessions_reserved_using_pin_group___get_connections_by_pins___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, "PinGroup1")
        )

        connections = reservation.get_connections(object, pin_or_relay_names=["A", "S1"])

        nidcpower_resource = "DCPower1/0, DCPower1/2, DCPower2/1"
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
        ]


def test___sessions_reserved_using_nested_pin_group___get_connections_by_pins___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, "PinGroup2")
        )

        connections = reservation.get_connections(object, pin_or_relay_names=["A", "C", "S1"])

        nidcpower_resource = "DCPower1/0, DCPower1/2, DCPower2/1"
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("C", 0, "SCOPE1", "2"),
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("C", 1, "SCOPE1", "2"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
        ]


def test___sessions_reserved_using_relay_group___get_connections_by_relays___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["RelayGroup1"])
        )

        connections = reservation.get_connections(
            object, pin_or_relay_names=["RelayUsingSameDriver", "SystemRelay"]
        )

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
        ]


def test___sessions_reserved_using_nested_relay_group___get_connections_by_relays___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, ["RelayGroup2"])
        )

        connections = reservation.get_connections(object, pin_or_relay_names=_PIN_MAP_C_RELAY_NAMES)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
            ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
        ]


def test___sessions_reserved___get_connections_by_pin_group___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        pin_group = ["PinGroup1"]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_group)
        )

        connections = reservation.get_connections(object, pin_or_relay_names=pin_group)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, "DCPower1/0, DCPower1/2, DCPower2/1", "DCPower1/0"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
        ]


def test___sessions_reserved___get_connections_by_nested_pin_group___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        pin_groups = ["PinGroup1", "PinGroup2"]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, pin_groups)
        )

        connections = reservation.get_connections(object, pin_or_relay_names=pin_groups)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, "DCPower1/0, DCPower1/2, DCPower2/1", "DCPower1/0"),
            ConnectionSubset("C", 0, "SCOPE1", "2"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
        ]


def test___sessions_reserved___get_connections_by_relay_group___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        relay_group = ["RelayGroup1"]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, relay_group)
        )

        connections = reservation.get_connections(object, pin_or_relay_names=relay_group)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
        ]


def test___sessions_reserved___get_connections_by_nested_relay_groups___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_C)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        relay_groups = ["RelayGroup1", "RelayGroup2"]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, relay_groups)
        )

        connections = reservation.get_connections(object, pin_or_relay_names=relay_groups)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
            ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
        ]


def test___reserve_sessions_with_multiplexer___get_connections_with_multiplexer___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_D)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_D_PIN_NAMES)
        )

        connections = reservation.get_connections_with_multiplexer(object, object)

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/3, DCPower2/2"
        assert [get_connection_subset_with_multiplexer(conn) for conn in connections] == [
            ConnectionSubset(
                "A", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C1->r0,C2->r0"
            ),
            ConnectionSubset(
                "B", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C3->r0,C4->r0"
            ),
            ConnectionSubset("C", 0, "SCOPE1", "0", "", ""),
            ConnectionSubset(
                "D", 0, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C3->r2,C4->r2"
            ),
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1", "", ""),
            ConnectionSubset(
                "B", 1, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C1->r2,C2->r2"
            ),
            ConnectionSubset("C", 1, "SCOPE1", "1", "", ""),
            ConnectionSubset("D", 1, nidcpower_resource, "DCPower1/3", "", ""),
        ]


def test___reserve_sessions_with_multiplexer___get_connections_with_multiplexer_by_pin___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_D)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_D_PIN_NAMES)
        )

        connections = [
            reservation.get_connections_with_multiplexer(object, object, pin_name)
            for pin_name in _PIN_MAP_D_PIN_NAMES
        ]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/3, DCPower2/2"
        assert [
            [get_connection_subset_with_multiplexer(conn) for conn in group]
            for group in connections
        ] == [
            [
                ConnectionSubset(
                    "A", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C1->r0,C2->r0"
                ),
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1", "", ""),
            ],
            [
                ConnectionSubset(
                    "B", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C3->r0,C4->r0"
                ),
                ConnectionSubset(
                    "B", 1, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C1->r2,C2->r2"
                ),
            ],
            [
                ConnectionSubset("C", 0, "SCOPE1", "0", "", ""),
                ConnectionSubset("C", 1, "SCOPE1", "1", "", ""),
            ],
            [
                ConnectionSubset(
                    "D", 0, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C3->r2,C4->r2"
                ),
                ConnectionSubset("D", 1, nidcpower_resource, "DCPower1/3", "", ""),
            ],
        ]


def test___reserve_sessions_with_multiplexer___get_connections_with_multiplexer_by_site___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_D)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_D_PIN_NAMES)
        )

        connections = [
            reservation.get_connections_with_multiplexer(object, object, sites=site)
            for site in [0, 1]
        ]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/3, DCPower2/2"
        assert [
            [get_connection_subset_with_multiplexer(conn) for conn in group]
            for group in connections
        ] == [
            [
                ConnectionSubset(
                    "A", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C1->r0,C2->r0"
                ),
                ConnectionSubset(
                    "B", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C3->r0,C4->r0"
                ),
                ConnectionSubset("C", 0, "SCOPE1", "0", "", ""),
                ConnectionSubset(
                    "D", 0, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C3->r2,C4->r2"
                ),
            ],
            [
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1", "", ""),
                ConnectionSubset(
                    "B", 1, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C1->r2,C2->r2"
                ),
                ConnectionSubset("C", 1, "SCOPE1", "1", "", ""),
                ConnectionSubset("D", 1, nidcpower_resource, "DCPower1/3", "", ""),
            ],
        ]


def test___reserve_session_with_multiplexer___get_connections_with_multiplexer_by_instrument_type___returns_connections(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    with ExitStack() as stack:
        pin_map_id = pin_map_client.update_pin_map(pin_map_directory / _PIN_MAP_D)
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(pin_map_context, _PIN_MAP_D_PIN_NAMES)
        )

        connections = [
            reservation.get_connections_with_multiplexer(
                object, object, instrument_type_id=instrument_type_id
            )
            for instrument_type_id in [INSTRUMENT_TYPE_NI_DCPOWER, INSTRUMENT_TYPE_NI_SCOPE]
        ]

        nidcpower_resource = "DCPower1/0, DCPower1/1, DCPower1/3, DCPower2/2"
        assert [
            [get_connection_subset_with_multiplexer(conn) for conn in group]
            for group in connections
        ] == [
            [
                ConnectionSubset(
                    "A", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C1->r0,C2->r0"
                ),
                ConnectionSubset(
                    "B", 0, nidcpower_resource, "DCPower1/0", "Multiplexer1", "C3->r0,C4->r0"
                ),
                ConnectionSubset(
                    "D", 0, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C3->r2,C4->r2"
                ),
                ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/1", "", ""),
                ConnectionSubset(
                    "B", 1, nidcpower_resource, "DCPower2/2", "Multiplexer2", "C1->r2,C2->r2"
                ),
                ConnectionSubset("D", 1, nidcpower_resource, "DCPower1/3", "", ""),
            ],
            [
                ConnectionSubset("C", 0, "SCOPE1", "0", "", ""),
                ConnectionSubset("C", 1, "SCOPE1", "1", "", ""),
            ],
        ]


def test___sessions_reserved_with_shared_pins_all_sites___get_connections___returns_connections_for_all_sites(
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
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("B", 0, nidcpower_resource, "DCPower2/1"),
            ConnectionSubset("C", 0, "SCOPE1", "2"),
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            ConnectionSubset("C", 1, "SCOPE1", "2"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
            ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
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
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 0, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("B", 0, nidcpower_resource, "DCPower2/1"),
            ConnectionSubset("C", 0, "SCOPE1", "2"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
            ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
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
        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("A", 1, nidcpower_resource, "DCPower1/0"),
            ConnectionSubset("B", 1, nidcpower_resource, "DCPower2/1"),
            ConnectionSubset("C", 1, "SCOPE1", "2"),
            ConnectionSubset("S1", -1, "SCOPE1", "1"),
            ConnectionSubset("S2", -1, nidcpower_resource, "DCPower1/2"),
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

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
            ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
            ConnectionSubset("RelayUsingDifferentDrivers", 1, "RelayDriver2", "K10"),
            ConnectionSubset("RelayUsingSameDriver", 1, "RelayDriver1", "K1"),
            ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
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

        assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
            [
                ConnectionSubset("RelayUsingDifferentDrivers", 0, "RelayDriver1", "K10"),
                ConnectionSubset("RelayUsingSameDriver", 0, "RelayDriver1", "K0"),
                ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
            ],
            [
                ConnectionSubset("RelayUsingDifferentDrivers", 1, "RelayDriver2", "K10"),
                ConnectionSubset("RelayUsingSameDriver", 1, "RelayDriver1", "K1"),
                ConnectionSubset("SystemRelay", -1, "RelayDriver1", "K60"),
            ],
        ]

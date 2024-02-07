import functools
from contextlib import ExitStack
from typing import List, Tuple
from unittest.mock import Mock

import pytest

from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.session_management import (
    MultiplexerSessionInformation,
    MultiSessionReservation,
    SingleSessionReservation,
)
from tests.unit._reservation_utils import (
    construct_session,
    create_grpc_multiplexer_session_infos,
    create_grpc_session_infos,
)
from tests.utilities import fake_multiplexer_driver
from tests.utilities.connection_subset import (
    ConnectionSubset,
    get_connection_subset_with_multiplexer,
)

create_nifake_session_infos = functools.partial(create_grpc_session_infos, "nifake")
create_nimultiplexer_session_infos = functools.partial(
    create_grpc_multiplexer_session_infos, "nimultiplexer"
)


def test___multiplexer_session_not_created___get_connection_with_multiplexer___raises_type_error(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1",
            site=2,
            channel="3",
            multiplexer_resource_name="Mux0",
            multiplexer_route="route1",
        )
        reservation = MultiSessionReservation(
            session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
        )
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(TypeError) as exc_info:
            _ = reservation.get_connection_with_multiplexer(object, fake_multiplexer_driver.Session)

        assert "Incorrect type for multiplexer session 'MyMultiplexer0'." in exc_info.value.args[0]
        assert (
            "Expected <class 'tests.utilities.fake_multiplexer_driver.Session'>, got <class 'NoneType'>."
            in exc_info.value.args[0]
        )


def test___multiplexer_session_not_created___get_connection_with_multiplexer_using_object_type___returns_connection(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1",
            site=2,
            channel="3",
            multiplexer_resource_name="Mux0",
            multiplexer_route="route1",
        )
        reservation = MultiSessionReservation(
            session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
        )
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        connection = reservation.get_connection_with_multiplexer(object, object)

        assert get_connection_subset_with_multiplexer(connection) == ConnectionSubset(
            "Pin1", 2, "Dev0", "3", "Mux0", "route1"
        )
        assert connection.multiplexer_session is None


def test___no_connection___get_connection_with_multiplexer___raises_value_error(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(0)
    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(0)
    reservation = MultiSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    with pytest.raises(ValueError) as exc_info:
        _ = reservation.get_connection_with_multiplexer(object, object)

    assert "No reserved connections matched the specified criteria." in exc_info.value.args[0]


def test___no_connections___get_connections_with_multiplexer_using_object_type___returns_empty_list(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(0)
    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(0)
    reservation = MultiSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    connections = reservation.get_connections_with_multiplexer(object, object)

    assert connections == []


def test___reservation_order___get_connections_with_multiplexer_in_specific_order___returns_connections_in_specified_order(
    session_management_client: Mock,
) -> None:
    (
        grpc_session_infos,
        grpc_multiplexer_session_infos,
    ) = _create_grpc_session_and_multiplexer_session_infos_for_ordering()
    reservation = MultiSessionReservation(
        session_management_client,
        grpc_session_infos,
        grpc_multiplexer_session_infos,
        reserved_pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        reserved_sites=[1, 0],
    )

    connections = [
        reservation.get_connections_with_multiplexer(
            object,
            object,
            pin_or_relay_names=["Pin1", "Pin3", "Pin2"],
            sites=[0, 1],
            instrument_type_id="nifake",
        ),
        reservation.get_connections_with_multiplexer(
            object, object, pin_or_relay_names=["Pin4"], sites=[0, 1], instrument_type_id="nibar"
        ),
    ]

    assert [
        [get_connection_subset_with_multiplexer(conn) for conn in group] for group in connections
    ] == [
        [
            ConnectionSubset("Pin1", 0, "Dev0", "0", "Mux0", "route1"),
            ConnectionSubset("Pin3", 0, "Dev1", "2", "Mux0", "route3"),
            ConnectionSubset("Pin2", 0, "Dev0", "1", "Mux0", "route2"),
            ConnectionSubset("Pin1", 1, "Dev1", "3", "Mux0", "route4"),
            ConnectionSubset("Pin3", 1, "Dev2", "5", "Mux0", "route6"),
            ConnectionSubset("Pin2", 1, "Dev2", "4", "Mux0", "route5"),
        ],
        [
            ConnectionSubset("Pin4", 0, "Dev3", "6", "Mux0", "route7"),
            ConnectionSubset("Pin4", 1, "Dev3", "7", "Mux0", "route8"),
        ],
    ]


def test___reservation_order___get_connections_with_multiplexer___returns_connections_in_reservation_order(
    session_management_client: Mock,
) -> None:
    (
        grpc_session_infos,
        grpc_multiplexer_session_infos,
    ) = _create_grpc_session_and_multiplexer_session_infos_for_ordering()
    reservation = MultiSessionReservation(
        session_management_client,
        grpc_session_infos,
        grpc_multiplexer_session_infos,
        reserved_pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        reserved_sites=[1, 0],
    )

    connections = reservation.get_connections_with_multiplexer(object, object)

    assert [get_connection_subset_with_multiplexer(conn) for conn in connections] == [
        ConnectionSubset("Pin3", 1, "Dev2", "5", "Mux0", "route6"),
        ConnectionSubset("Pin1", 1, "Dev1", "3", "Mux0", "route4"),
        ConnectionSubset("Pin4", 1, "Dev3", "7", "Mux0", "route8"),
        ConnectionSubset("Pin2", 1, "Dev2", "4", "Mux0", "route5"),
        ConnectionSubset("Pin3", 0, "Dev1", "2", "Mux0", "route3"),
        ConnectionSubset("Pin1", 0, "Dev0", "0", "Mux0", "route1"),
        ConnectionSubset("Pin4", 0, "Dev3", "6", "Mux0", "route7"),
        ConnectionSubset("Pin2", 0, "Dev0", "1", "Mux0", "route2"),
    ]


def test___no_reservation_order___get_connections_with_multiplexer___returns_connections_in_default_order(
    session_management_client: Mock,
) -> None:
    (
        grpc_session_infos,
        grpc_multiplexer_session_infos,
    ) = _create_grpc_session_and_multiplexer_session_infos_for_ordering()
    reservation = MultiSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    connections = reservation.get_connections_with_multiplexer(object, object)

    assert [get_connection_subset_with_multiplexer(conn) for conn in connections] == [
        ConnectionSubset("Pin1", 0, "Dev0", "0", "Mux0", "route1"),
        ConnectionSubset("Pin2", 0, "Dev0", "1", "Mux0", "route2"),
        ConnectionSubset("Pin3", 0, "Dev1", "2", "Mux0", "route3"),
        ConnectionSubset("Pin4", 0, "Dev3", "6", "Mux0", "route7"),
        ConnectionSubset("Pin1", 1, "Dev1", "3", "Mux0", "route4"),
        ConnectionSubset("Pin2", 1, "Dev2", "4", "Mux0", "route5"),
        ConnectionSubset("Pin3", 1, "Dev2", "5", "Mux0", "route6"),
        ConnectionSubset("Pin4", 1, "Dev3", "7", "Mux0", "route8"),
    ]


def test___partial_multiplexed_connections___get_connections_with_multiplexer_using_session_type___returns_all_specified_pin_connections(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(1)
    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
    grpc_session_infos[0].channel_mappings.add(
        pin_or_relay_name="Pin2",
        site=0,
        channel="1",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route1",
    )
    grpc_session_infos[0].channel_mappings.add(
        pin_or_relay_name="Pin3",
        site=1,
        channel="1",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route2",
    )
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin4", site=0, channel="3")
    reservation = MultiSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    # TODO: Update the multiplexer_session_type to fake_multiplexer_driver.Session once the
    # initialize_multiplexer API gets added.
    connections = reservation.get_connections_with_multiplexer(object, object)

    assert [get_connection_subset_with_multiplexer(conn) for conn in connections] == [
        ConnectionSubset("Pin1", 0, "Dev0", "0", "", ""),
        ConnectionSubset("Pin2", 0, "Dev0", "1", "Mux0", "route1"),
        ConnectionSubset("Pin4", 0, "Dev0", "3", "", ""),
        ConnectionSubset("Pin3", 1, "Dev0", "1", "Mux0", "route2"),
    ]


def test____connection_with_no_multiplexer___get_connection_with_multiplexer___returns_connection(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(1)
    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
    reservation = SingleSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    connection = reservation.get_connection_with_multiplexer(object, object)

    assert get_connection_subset_with_multiplexer(connection) == ConnectionSubset(
        "Pin1", 0, "Dev0", "0", "", ""
    )


def test____connections_with_no_multiplexer___get_connections_with_multiplexer___returns_all_connections(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(1)
    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin2", site=1, channel="2")
    reservation = SingleSessionReservation(
        session_management_client, grpc_session_infos, grpc_multiplexer_session_infos
    )

    connections = reservation.get_connections_with_multiplexer(object, object)

    assert [get_connection_subset_with_multiplexer(conn) for conn in connections] == [
        ConnectionSubset("Pin1", 0, "Dev0", "0", "", ""),
        ConnectionSubset("Pin2", 1, "Dev0", "2", "", ""),
    ]


def test___reserved_single_session_with_single_multiplexer___get_multiplexer_session_info___returns_multiplexer_session_info_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = SingleSessionReservation(
        session_management_client,
        create_nifake_session_infos(1),
        create_nimultiplexer_session_infos(1),
    )
    expected_multiplexer_session_info = MultiplexerSessionInformation(
        "MyMultiplexer0", "Mux0", "nimultiplexer", False, None
    )

    assert reservation.multiplexer_session_info[0] == expected_multiplexer_session_info
    assert reservation.multiplexer_session_info[0].session is None


def test___reserved_single_session_with_multiple_multiplexers___get_multiplexer_session_info___returns_multiplexer_session_info_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = SingleSessionReservation(
        session_management_client,
        create_nifake_session_infos(1),
        create_nimultiplexer_session_infos(3),
    )
    expected_multiplexer_session_infos = [
        MultiplexerSessionInformation("MyMultiplexer0", "Mux0", "nimultiplexer", False, None),
        MultiplexerSessionInformation("MyMultiplexer1", "Mux1", "nimultiplexer", False, None),
        MultiplexerSessionInformation("MyMultiplexer2", "Mux2", "nimultiplexer", False, None),
    ]

    assert reservation.multiplexer_session_info == expected_multiplexer_session_infos
    assert all([info.session is None for info in reservation.multiplexer_session_info])


def test___reserved_multiple_sessions_with_single_multiplexer___get_multiplexer_session_info___returns_multiplexer_session_info_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client,
        create_nifake_session_infos(2),
        create_nimultiplexer_session_infos(1),
    )
    expected_multiplexer_session_info = MultiplexerSessionInformation(
        "MyMultiplexer0", "Mux0", "nimultiplexer", False, None
    )

    assert reservation.multiplexer_session_info[0] == expected_multiplexer_session_info
    assert reservation.multiplexer_session_info[0].session is None


def test___reserved_multiple_sessions_with_multiple_multiplexers___get_multiplexer_session_info___returns_multiplexer_session_info_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client,
        create_nifake_session_infos(2),
        create_nimultiplexer_session_infos(3),
    )
    expected_multiplexer_session_infos = [
        MultiplexerSessionInformation("MyMultiplexer0", "Mux0", "nimultiplexer", False, None),
        MultiplexerSessionInformation("MyMultiplexer1", "Mux1", "nimultiplexer", False, None),
        MultiplexerSessionInformation("MyMultiplexer2", "Mux2", "nimultiplexer", False, None),
    ]

    assert reservation.multiplexer_session_info == expected_multiplexer_session_infos
    assert all([info.session is None for info in reservation.multiplexer_session_info])


def _create_grpc_session_and_multiplexer_session_infos_for_ordering() -> Tuple[
    List[session_management_service_pb2.SessionInformation],
    List[session_management_service_pb2.MultiplexerSessionInformation],
]:
    grpc_session_infos = create_nifake_session_infos(4)
    grpc_session_infos[0].channel_mappings.add(
        pin_or_relay_name="Pin1",
        site=0,
        channel="0",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route1",
    )
    grpc_session_infos[0].channel_mappings.add(
        pin_or_relay_name="Pin2",
        site=0,
        channel="1",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route2",
    )
    grpc_session_infos[1].channel_mappings.add(
        pin_or_relay_name="Pin3",
        site=0,
        channel="2",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route3",
    )
    grpc_session_infos[1].channel_mappings.add(
        pin_or_relay_name="Pin1",
        site=1,
        channel="3",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route4",
    )
    grpc_session_infos[2].channel_mappings.add(
        pin_or_relay_name="Pin2",
        site=1,
        channel="4",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route5",
    )
    grpc_session_infos[2].channel_mappings.add(
        pin_or_relay_name="Pin3",
        site=1,
        channel="5",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route6",
    )
    grpc_session_infos[3].channel_mappings.add(
        pin_or_relay_name="Pin4",
        site=0,
        channel="6",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route7",
    )
    grpc_session_infos[3].channel_mappings.add(
        pin_or_relay_name="Pin4",
        site=1,
        channel="7",
        multiplexer_resource_name="Mux0",
        multiplexer_route="route8",
    )
    grpc_session_infos[3].instrument_type_id = "nibar"

    grpc_multiplexer_session_infos = create_nimultiplexer_session_infos(1)
    return (grpc_session_infos, grpc_multiplexer_session_infos)

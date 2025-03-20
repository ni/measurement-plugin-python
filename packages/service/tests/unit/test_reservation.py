from __future__ import annotations

import functools
from contextlib import ExitStack
from typing import Any
from unittest.mock import Mock

import pytest

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurement_plugin_sdk_service.session_management import (
    SITE_SYSTEM_PINS,
    MultiSessionReservation,
    SessionInformation,
    SingleSessionReservation,
)
from tests.unit._reservation_utils import construct_session, create_grpc_session_infos
from tests.utilities import fake_driver
from tests.utilities.connection_subset import ConnectionSubset, get_connection_subset

create_nifake_session_infos = functools.partial(create_grpc_session_infos, "nifake")
create_nifoo_session_infos = functools.partial(create_grpc_session_infos, "nifoo")


def test___single_session_info___initialize_session___session_info_yielded(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.initialize_session(construct_session, "nifake") as session_info:
        assert session_info.session_name == "MySession0"
        assert session_info.resource_name == "Dev0"
        assert session_info.instrument_type_id == "nifake"


def test___single_session_info___initialize_session___session_created(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.initialize_session(construct_session, "nifake") as session_info:
        assert isinstance(session_info.session, fake_driver.Session)
        assert session_info.session.resource_name == "Dev0"


def test___single_session_info___initialize_session___session_lifetime_tracked(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.initialize_session(construct_session, "nifake") as session_info:
        assert reservation._session_cache["MySession0"] is session_info.session
        assert not session_info.session.is_closed

    assert len(reservation._session_cache) == 0
    assert session_info.session.is_closed


def test___empty_instrument_type_id___initialize_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with pytest.raises(ValueError) as exc_info:
        with reservation.initialize_session(construct_session, ""):
            pass

    assert "This method requires an instrument type ID." in exc_info.value.args[0]


def test___no_session_infos___initialize_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(0))

    with pytest.raises(ValueError) as exc_info:
        with reservation.initialize_session(construct_session, "nifake"):
            pass

    assert "No reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___multiple_session_infos___initialize_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(2))

    with pytest.raises(ValueError) as exc_info:
        with reservation.initialize_session(construct_session, "nifake"):
            pass

    assert (
        "Too many reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]
    )


def test___session_already_exists___initialize_session___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.initialize_session(construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.initialize_session(construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___initialize_session___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifoo_session_infos(2)
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.initialize_session(
        construct_session, "nifoo"
    ) as nifoo_info, reservation.initialize_session(construct_session, "nibar") as nibar_info:
        assert nifoo_info.session_name == "MySession0"
        assert nifoo_info.instrument_type_id == "nifoo"
        assert nibar_info.session_name == "MySession1"
        assert nibar_info.instrument_type_id == "nibar"


def test___multiple_session_infos___initialize_sessions___session_infos_yielded(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.initialize_sessions(construct_session, "nifake") as session_infos:
        assert [info.session_name for info in session_infos] == [
            "MySession0",
            "MySession1",
            "MySession2",
        ]
        assert [info.resource_name for info in session_infos] == ["Dev0", "Dev1", "Dev2"]
        assert [info.instrument_type_id for info in session_infos] == ["nifake", "nifake", "nifake"]


def test___multiple_session_infos___initialize_sessions___sessions_created(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.initialize_sessions(construct_session, "nifake") as session_infos:
        assert all([isinstance(info.session, fake_driver.Session) for info in session_infos])
        assert [info.session.resource_name for info in session_infos] == ["Dev0", "Dev1", "Dev2"]


def test___multiple_session_infos___initialize_sessions___session_lifetime_tracked(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.initialize_sessions(construct_session, "nifake") as session_infos:
        assert reservation._session_cache["MySession0"] is session_infos[0].session
        assert reservation._session_cache["MySession1"] is session_infos[1].session
        assert reservation._session_cache["MySession2"] is session_infos[2].session
        assert all([not info.session.is_closed for info in session_infos])

    assert len(reservation._session_cache) == 0
    assert all([info.session.is_closed for info in session_infos])


def test___empty_instrument_type_id___initialize_sessions___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with pytest.raises(ValueError) as exc_info:
        with reservation.initialize_sessions(construct_session, ""):
            pass

    assert "This method requires an instrument type ID." in exc_info.value.args[0]


def test___no_session_infos___initialize_sessions___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, [])

    with pytest.raises(ValueError) as exc_info:
        with reservation.initialize_sessions(construct_session, "nifake"):
            pass

    assert "No reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___session_already_exists___initialize_sessions___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.initialize_sessions(construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.initialize_sessions(construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___initialize_sessions___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifoo_session_infos(3)
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.initialize_sessions(
        construct_session, "nifoo"
    ) as nifoo_infos, reservation.initialize_sessions(construct_session, "nibar") as nibar_infos:
        assert [info.session_name for info in nifoo_infos] == ["MySession0", "MySession2"]
        assert [info.instrument_type_id for info in nifoo_infos] == ["nifoo", "nifoo"]
        assert [info.session_name for info in nibar_infos] == ["MySession1"]
        assert [info.instrument_type_id for info in nibar_infos] == ["nibar"]


def test___single_connection___get_connection___connection_returned(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        connection = reservation.get_connection(fake_driver.Session)

        assert connection.pin_or_relay_name == "Pin1"
        assert connection.site == 2
        assert connection.channel_name == "3"
        assert connection.session_info == session_info


def test___session_reserved_using_pin_group___get_connection_by_pin___returns_connection(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin2", site=2, channel="2")
        group_mappings = {"PinGroup1": ["Pin1", "Pin2"]}
        reservation = MultiSessionReservation(
            session_management_client,
            grpc_session_infos,
            pin_or_relay_group_mappings=group_mappings,
            reserved_pin_or_relay_names=["PinGroup1"],
        )
        session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        connection = reservation.get_connection(fake_driver.Session, pin_or_relay_name="Pin2")

        assert connection.pin_or_relay_name == "Pin2"
        assert connection.site == 2
        assert connection.channel_name == "2"
        assert connection.session_info == session_info


def test___duplicate_pins___get_connections___returns_single_connection(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        connections = reservation.get_connections(
            fake_driver.Session, pin_or_relay_names=["Pin1", "Pin1"]
        )

        assert len(connections) == 1
        assert connections[0].pin_or_relay_name == "Pin1"
        assert connections[0].site == 2
        assert connections[0].channel_name == "3"
        assert connections[0].session_info == session_info


def test___session_reserved___get_connections_by_pin_group___returns_connections(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin2", site=2, channel="2")
        group_mappings = {"PinGroup1": ["Pin1", "Pin2"]}
        reservation = MultiSessionReservation(
            session_management_client,
            grpc_session_infos,
            pin_or_relay_group_mappings=group_mappings,
            reserved_pin_or_relay_names=["PinGroup1"],
        )
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        connections = reservation.get_connections(
            fake_driver.Session, pin_or_relay_names=["PinGroup1"]
        )

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("Pin1", 2, "Dev0", "3"),
            ConnectionSubset("Pin2", 2, "Dev0", "2"),
        ]


def test___multiple_connections___get_connection___value_error_raised(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(ValueError) as exc_info:
            _ = reservation.get_connection(fake_driver.Session)

        assert (
            "Too many reserved connections matched the specified criteria."
            in exc_info.value.args[0]
        )


@pytest.mark.parametrize(
    "kwargs,expected_message",
    [
        (
            {"pin_or_relay_name": ["Pin1"]},
            "The pin_or_relay_name parameter must be a str or None, not ['Pin1'].",
        ),
        ({"site": [2]}, "The site parameter must be an int or None, not [2]."),
        (
            {"instrument_type_id": ["nifake"]},
            "The instrument_type_id parameter must be a str or None, not ['nifake'].",
        ),
    ],
)
def test___invalid_argument_type___get_connection___type_error_raised(
    kwargs: dict[str, Any],
    expected_message: str,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(TypeError) as exc_info:
            _ = reservation.get_connection(fake_driver.Session, **kwargs)

        assert expected_message in exc_info.value.args[0]


def test___wrong_pins___get_connections___value_error_raised(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(ValueError) as exc_info:
            _ = reservation.get_connections(fake_driver.Session, ["Pin1", "Pin2", "Pin3"])

        assert (
            "No reserved connections matched pin or relay name(s) 'Pin2', 'Pin3'."
            in exc_info.value.args[0]
        )


def test___wrong_sites___get_connections___value_error_raised(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(ValueError) as exc_info:
            _ = reservation.get_connections(fake_driver.Session, sites=[1, 2, 3])

        assert "No reserved connections matched site(s) 1, 3." in exc_info.value.args[0]


def test___wrong_instrument_type_id___get_connections___value_error_raised(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(ValueError) as exc_info:
            _ = reservation.get_connections(fake_driver.Session, instrument_type_id="nifoo")

        assert (
            "No reserved connections matched instrument type ID 'nifoo'." in exc_info.value.args[0]
        )


@pytest.mark.parametrize("pin_name,site,channel_name", [("Pin1", 2, "3"), ("Pin4", 5, "6")])
def test___multiple_connections___get_connection_with_pin_name___connection_returned(
    session_management_client: Mock,
    pin_name: str,
    site: int,
    channel_name: str,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        connection = reservation.get_connection(fake_driver.Session, pin_name)

        assert connection.pin_or_relay_name == pin_name
        assert connection.site == site
        assert connection.channel_name == channel_name
        assert connection.session_info == session_info


@pytest.mark.parametrize("pin_name,site,channel_name", [("Pin1", 2, "3"), ("Pin4", 5, "6")])
def test___multiple_connections___get_connection_with_site___connection_returned(
    session_management_client: Mock,
    pin_name: str,
    site: int,
    channel_name: str,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        connection = reservation.get_connection(fake_driver.Session, site=site)

        assert connection.pin_or_relay_name == pin_name
        assert connection.site == site
        assert connection.channel_name == channel_name
        assert connection.session_info == session_info


@pytest.mark.parametrize(
    "instrument_type_id,pin_name,site,channel_name",
    [("nifoo", "Pin1", 2, "3"), ("nibar", "Pin4", 5, "6")],
)
def test___heterogenous_session_infos___get_connection_with_instrument_type_id___connection_returned(
    session_management_client: Mock,
    instrument_type_id: str,
    pin_name: str,
    site: int,
    channel_name: str,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifoo_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        grpc_session_infos[1].instrument_type_id = "nibar"
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        nifoo_info = stack.enter_context(reservation.initialize_session(construct_session, "nifoo"))
        nibar_info = stack.enter_context(reservation.initialize_session(construct_session, "nibar"))

        connection = reservation.get_connection(
            fake_driver.Session, instrument_type_id=instrument_type_id
        )

        assert connection.pin_or_relay_name == pin_name
        assert connection.site == site
        assert connection.channel_name == channel_name
        if instrument_type_id == "nifoo":
            assert connection.session_info == nifoo_info
        else:
            assert connection.session_info == nibar_info


def test___heterogenous_session_infos___get_connections___connections_returned(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifoo_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        grpc_session_infos[1].instrument_type_id = "nibar"
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        nifoo_info = stack.enter_context(reservation.initialize_session(construct_session, "nifoo"))
        nibar_info = stack.enter_context(reservation.initialize_session(construct_session, "nibar"))

        connections = reservation.get_connections(fake_driver.Session)

        assert [get_connection_subset(conn) for conn in connections] == [
            ConnectionSubset("Pin1", 2, "Dev0", "3"),
            ConnectionSubset("Pin4", 5, "Dev1", "6"),
        ]
        assert [conn.session for conn in connections] == [nifoo_info.session, nibar_info.session]


@pytest.mark.parametrize(
    "kwargs,expected_message",
    [
        (
            {"pin_or_relay_names": "Pin1", "sites": 5},
            "No reserved connections matched pin or relay name(s) 'Pin1' with the specified criteria: site(s) 5",
        ),
        (
            {"pin_or_relay_names": "Pin4", "sites": 2},
            "No reserved connections matched pin or relay name(s) 'Pin4' with the specified criteria: site(s) 2",
        ),
        (
            {"pin_or_relay_names": "Pin1", "instrument_type_id": "nibar"},
            "No reserved connections matched pin or relay name(s) 'Pin1' with the specified criteria: instrument type ID 'nibar'",
        ),
        (
            {"pin_or_relay_names": ["Pin1", "Pin4"], "instrument_type_id": "nibar"},
            "No reserved connections matched pin or relay name(s) 'Pin1' with the specified criteria: instrument type ID 'nibar'",
        ),
        (
            {"sites": 2, "instrument_type_id": "nibar"},
            "No reserved connections matched the specified criteria: site(s) 2; instrument type ID 'nibar'",
        ),
    ],
)
def test___heterogenous_session_infos___get_connections_with_partially_matching_criteria___value_error_raised(
    kwargs: dict[str, Any],
    expected_message: str,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifoo_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin4", site=5, channel="6")
        grpc_session_infos[1].instrument_type_id = "nibar"
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifoo"))
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nibar"))

        with pytest.raises(ValueError) as exc_info:
            _ = reservation.get_connections(fake_driver.Session, **kwargs)

        assert expected_message in exc_info.value.args[0]


def test___wrong_session_type___get_connection___type_error_raised(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nifake_session_infos(1)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        _ = stack.enter_context(reservation.initialize_session(construct_session, "nifake"))

        with pytest.raises(TypeError) as exc_info:
            _ = reservation.get_connection(int)

        assert "Incorrect type for session 'MySession0'." in exc_info.value.args[0]
        assert (
            "Expected <class 'int'>, got <class 'tests.utilities.fake_driver.Session'>."
            in exc_info.value.args[0]
        )


def test___session_not_created___get_connection___type_error_raised(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(1)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with pytest.raises(TypeError) as exc_info:
        _ = reservation.get_connection(fake_driver.Session)

    assert "Incorrect type for session 'MySession0'." in exc_info.value.args[0]
    assert (
        "Expected <class 'tests.utilities.fake_driver.Session'>, got <class 'NoneType'>."
        in exc_info.value.args[0]
    )


def test___session_not_created___get_connection_with_session_type_object___connection_returned(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(1)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=2, channel="3")
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connection = reservation.get_connection(object)

    assert connection.pin_or_relay_name == "Pin1"
    assert connection.site == 2
    assert connection.channel_name == "3"
    assert connection.session is None


def test___no_connections___get_connection_with_session_type_object___value_error_raised(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(0)
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with pytest.raises(ValueError) as exc_info:
        _ = reservation.get_connection(object)

    assert "No reserved connections matched the specified criteria." in exc_info.value.args[0]


def test___no_connections___get_connections_with_session_type_object___empty_list_returned(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifake_session_infos(0)
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = reservation.get_connections(object)

    assert connections == []


def test___reservation_order___get_connections_with_specified_order___connections_returned_in_specified_order(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_for_ordering()
    reservation = MultiSessionReservation(
        session_management_client,
        grpc_session_infos,
        reserved_pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        reserved_sites=[1, 0],
    )

    connections = [
        reservation.get_connections(
            object,
            pin_or_relay_names=["Pin1", "Pin3", "Pin2"],
            sites=[0, 1],
            instrument_type_id="nifoo",
        ),
        reservation.get_connections(
            object, pin_or_relay_names=["Pin4"], sites=[0, 1], instrument_type_id="nibar"
        ),
    ]

    assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
        [
            ConnectionSubset("Pin1", 0, "Dev0", "0"),
            ConnectionSubset("Pin3", 0, "Dev1", "2"),
            ConnectionSubset("Pin2", 0, "Dev0", "1"),
            ConnectionSubset("Pin1", 1, "Dev1", "3"),
            ConnectionSubset("Pin3", 1, "Dev2", "5"),
            ConnectionSubset("Pin2", 1, "Dev2", "4"),
        ],
        [
            ConnectionSubset("Pin4", 0, "Dev3", "6"),
            ConnectionSubset("Pin4", 1, "Dev3", "7"),
        ],
    ]


def test___reservation_order___get_connections___connections_returned_in_reservation_order(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_for_ordering()
    reservation = MultiSessionReservation(
        session_management_client,
        grpc_session_infos,
        reserved_pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        reserved_sites=[1, 0],
    )

    connections = reservation.get_connections(object)

    assert [get_connection_subset(conn) for conn in connections] == [
        ConnectionSubset("Pin3", 1, "Dev2", "5"),
        ConnectionSubset("Pin1", 1, "Dev1", "3"),
        ConnectionSubset("Pin4", 1, "Dev3", "7"),
        ConnectionSubset("Pin2", 1, "Dev2", "4"),
        ConnectionSubset("Pin3", 0, "Dev1", "2"),
        ConnectionSubset("Pin1", 0, "Dev0", "0"),
        ConnectionSubset("Pin4", 0, "Dev3", "6"),
        ConnectionSubset("Pin2", 0, "Dev0", "1"),
    ]


def test___no_reservation_order___get_connections___connections_returned_in_default_order(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_for_ordering()
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = reservation.get_connections(object)

    assert [get_connection_subset(conn) for conn in connections] == [
        ConnectionSubset("Pin1", 0, "Dev0", "0"),
        ConnectionSubset("Pin2", 0, "Dev0", "1"),
        ConnectionSubset("Pin3", 0, "Dev1", "2"),
        ConnectionSubset("Pin4", 0, "Dev3", "6"),
        ConnectionSubset("Pin1", 1, "Dev1", "3"),
        ConnectionSubset("Pin2", 1, "Dev2", "4"),
        ConnectionSubset("Pin3", 1, "Dev2", "5"),
        ConnectionSubset("Pin4", 1, "Dev3", "7"),
    ]


def test___system_pins___get_connections___system_pins_returned_in_default_order(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_with_system_pins()
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = reservation.get_connections(object)

    assert [get_connection_subset(conn) for conn in connections] == [
        ConnectionSubset("SystemPin1", -1, "Dev0", "4"),
        ConnectionSubset("SystemPin2", -1, "Dev1", "5"),
        ConnectionSubset("Pin1", 0, "Dev0", "0"),
        ConnectionSubset("Pin2", 0, "Dev0", "1"),
        ConnectionSubset("Pin1", 1, "Dev1", "2"),
        ConnectionSubset("Pin2", 1, "Dev1", "3"),
    ]


def test___system_pins___get_connections_by_site___system_pins_also_returned(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_with_system_pins()
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = [reservation.get_connections(object, sites=site) for site in [0, 1]]

    assert [[get_connection_subset(conn) for conn in group] for group in connections] == [
        [
            ConnectionSubset("Pin1", 0, "Dev0", "0"),
            ConnectionSubset("Pin2", 0, "Dev0", "1"),
            ConnectionSubset("SystemPin1", -1, "Dev0", "4"),
            ConnectionSubset("SystemPin2", -1, "Dev1", "5"),
        ],
        [
            ConnectionSubset("Pin1", 1, "Dev1", "2"),
            ConnectionSubset("Pin2", 1, "Dev1", "3"),
            ConnectionSubset("SystemPin1", -1, "Dev0", "4"),
            ConnectionSubset("SystemPin2", -1, "Dev1", "5"),
        ],
    ]


def test___system_pins___get_connection_with_system_pins_constant___only_system_pins_returned(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_with_system_pins()
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = reservation.get_connections(object, sites=SITE_SYSTEM_PINS)

    assert [get_connection_subset(conn) for conn in connections] == [
        ConnectionSubset("SystemPin1", -1, "Dev0", "4"),
        ConnectionSubset("SystemPin2", -1, "Dev1", "5"),
    ]


def test___system_pins___get_connection_with_site_list___system_pins_returned_in_specified_order(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos_with_system_pins()
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    connections = reservation.get_connections(object, sites=[0, SITE_SYSTEM_PINS, 1])

    assert [get_connection_subset(conn) for conn in connections] == [
        ConnectionSubset("Pin1", 0, "Dev0", "0"),
        ConnectionSubset("Pin2", 0, "Dev0", "1"),
        ConnectionSubset("SystemPin1", -1, "Dev0", "4"),
        ConnectionSubset("SystemPin2", -1, "Dev1", "5"),
        ConnectionSubset("Pin1", 1, "Dev1", "2"),
        ConnectionSubset("Pin2", 1, "Dev1", "3"),
    ]


def test___single_session_reserved___get_session_info___session_info_returned_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = SingleSessionReservation(
        session_management_client, create_nifake_session_infos(1)
    )
    expected_session_info = SessionInformation("MySession0", "Dev0", "", "nifake", False, [], None)

    assert reservation.session_info == expected_session_info
    assert reservation.session_info.session is None


def test___single_session_created___get_session_info___session_info_returned_with_valid_session(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        reservation = SingleSessionReservation(
            session_management_client, create_nifake_session_infos(1)
        )
        expected_session_info = stack.enter_context(
            reservation.initialize_session(construct_session, "nifake")
        )

        assert reservation.session_info == expected_session_info
        assert isinstance(reservation.session_info.session, fake_driver.Session)


def test___multiple_sessions_reserved___get_session_info___session_info_returned_with_null_session(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))
    expected_session_infos = [
        SessionInformation("MySession0", "Dev0", "", "nifake", False, [], None),
        SessionInformation("MySession1", "Dev1", "", "nifake", False, [], None),
        SessionInformation("MySession2", "Dev2", "", "nifake", False, [], None),
    ]

    assert reservation.session_info == expected_session_infos
    assert all([info.session is None for info in reservation.session_info])


def test___multiple_sessions_created___get_session_info___session_info_returned_with_valid_session(
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        reservation = MultiSessionReservation(
            session_management_client, create_nifake_session_infos(3)
        )
        expected_session_infos = stack.enter_context(
            reservation.initialize_sessions(construct_session, "nifake")
        )

        assert reservation.session_info == expected_session_infos
        assert all(
            [isinstance(info.session, fake_driver.Session) for info in reservation.session_info]
        )


def _create_grpc_session_infos_for_ordering() -> (
    list[session_management_service_pb2.SessionInformation]
):
    grpc_session_infos = create_nifoo_session_infos(4)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin2", site=0, channel="1")
    grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin3", site=0, channel="2")
    grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin1", site=1, channel="3")
    grpc_session_infos[2].channel_mappings.add(pin_or_relay_name="Pin2", site=1, channel="4")
    grpc_session_infos[2].channel_mappings.add(pin_or_relay_name="Pin3", site=1, channel="5")
    grpc_session_infos[3].channel_mappings.add(pin_or_relay_name="Pin4", site=0, channel="6")
    grpc_session_infos[3].channel_mappings.add(pin_or_relay_name="Pin4", site=1, channel="7")
    grpc_session_infos[3].instrument_type_id = "nibar"
    return grpc_session_infos


def _create_grpc_session_infos_with_system_pins() -> (
    list[session_management_service_pb2.SessionInformation]
):
    grpc_session_infos = create_nifoo_session_infos(2)
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="SystemPin1", site=-1, channel="4")
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
    grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin2", site=0, channel="1")
    grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin1", site=1, channel="2")
    grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin2", site=1, channel="3")
    grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="SystemPin2", site=-1, channel="5")
    return grpc_session_infos

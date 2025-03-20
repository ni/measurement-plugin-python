from __future__ import annotations

import functools
from contextlib import ExitStack
from typing import Any
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._configuration import NISwitchOptions
from ni_measurement_plugin_sdk_service.session_management import (
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    MultiSessionReservation,
    SessionInitializationBehavior,
)
from tests.unit._drivers._driver_utils import create_mock_session, create_mock_sessions
from tests.unit._reservation_utils import create_grpc_session_infos

try:
    import niswitch
except ImportError:
    niswitch = None

pytestmark = pytest.mark.skipif(niswitch is None, reason="Requires 'niswitch' package.")

if niswitch:
    create_mock_niswitch_session = functools.partial(create_mock_session, niswitch.Session)
    create_mock_niswitch_sessions = functools.partial(create_mock_sessions, niswitch.Session)
    create_niswitch_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_RELAY_DRIVER
    )


def test___single_session_info___initialize_niswitch_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.initialize_niswitch_session(
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
    ) as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="Dev0",
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
        grpc_options=ANY,
    )


def test___multiple_session_infos___initialize_niswitch_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(2)
    )
    sessions = create_mock_niswitch_sessions(3)
    session_new.side_effect = sessions

    with reservation.initialize_niswitch_sessions(
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
    ) as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_new.assert_any_call(
        niswitch.Session,
        resource_name="Dev0",
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
        grpc_options=ANY,
    )
    session_new.assert_any_call(
        niswitch.Session,
        resource_name="Dev1",
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
        grpc_options=ANY,
    )


# For NI-SWITCH, we set resource_name to "" when simulate is True.
@pytest.mark.parametrize("simulate,expected_resource_name", [(False, "Dev0"), (True, "")])
def test___optional_args___initialize_niswitch_session___optional_args_passed(
    simulate: bool,
    expected_resource_name: str,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.initialize_niswitch_session(
        topology="2567/Independent",
        simulate=simulate,
        reset_device=True,
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name=expected_resource_name,
        topology="2567/Independent",
        simulate=simulate,
        reset_device=True,
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___initialize_niswitch_session___simulation_options_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    _set_niswitch_simulation_options(mocker, True, "2567/Independent")
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.initialize_niswitch_session():
        pass

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="",
        topology="2567/Independent",
        simulate=True,
        reset_device=False,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___initialize_niswitch_session___optional_args_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    _set_niswitch_simulation_options(mocker, True, "2567/Independent")
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.initialize_niswitch_session(
        topology="2529/2-Wire 4x32 Matrix", simulate=False, reset_device=True
    ):
        pass

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="Dev0",
        topology="2529/2-Wire 4x32 Matrix",
        simulate=False,
        reset_device=True,
        grpc_options=ANY,
    )


# The NI-SWITCH version of the get_connection(s) test cases uses relay names.
@pytest.mark.parametrize(
    "kwargs,expected_channel_name,expected_session_index",
    [
        ({"relay_name": "Relay1", "site": 0}, "K0", 0),
        ({"relay_name": "Relay2", "site": 0}, "K1", 0),
        ({"relay_name": "Relay1", "site": 1}, "K2", 0),
        ({"relay_name": "Relay2", "site": 1}, "K0", 1),
    ],
)
def test___session_created___get_niswitch_connection___connection_returned(
    kwargs: dict[str, Any],
    expected_channel_name: str,
    expected_session_index: int,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_niswitch_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay1", site=0, channel="K0")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay2", site=0, channel="K1")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay1", site=1, channel="K2")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Relay2", site=1, channel="K0")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        sessions = create_mock_niswitch_sessions(2)
        session_new.side_effect = sessions
        session_infos = stack.enter_context(reservation.initialize_niswitch_sessions())

        connection = reservation.get_niswitch_connection(**kwargs)

        assert connection.channel_name == expected_channel_name
        assert connection.session is session_infos[expected_session_index].session


@pytest.mark.parametrize(
    "kwargs,expected_channel_names,expected_session_indices",
    [
        ({}, ["K0", "K1", "K2", "K0"], [0, 0, 0, 1]),
        ({"relay_names": "Relay1"}, ["K0", "K2"], [0, 0]),
        ({"relay_names": "Relay2"}, ["K1", "K0"], [0, 1]),
        ({"sites": 0}, ["K0", "K1"], [0, 0]),
        ({"sites": 1}, ["K2", "K0"], [0, 1]),
        (
            {"relay_names": ["Relay2", "Relay1"], "sites": [1, 0]},
            ["K0", "K2", "K1", "K0"],
            [1, 0, 0, 0],
        ),
    ],
)
def test___session_created___get_niswitch_connections___connections_returned(
    kwargs: dict[str, Any],
    expected_channel_names: list[str],
    expected_session_indices: list[int],
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_niswitch_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay1", site=0, channel="K0")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay2", site=0, channel="K1")
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Relay1", site=1, channel="K2")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Relay2", site=1, channel="K0")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        sessions = create_mock_niswitch_sessions(2)
        session_new.side_effect = sessions
        session_infos = stack.enter_context(reservation.initialize_niswitch_sessions())

        connections = reservation.get_niswitch_connections(**kwargs)

        assert [conn.channel_name for conn in connections] == expected_channel_names
        assert [conn.session for conn in connections] == [
            session_infos[i].session for i in expected_session_indices
        ]


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("niswitch.Session.__new__", autospec=True)


def _set_niswitch_simulation_options(mocker: MockerFixture, simulate: bool, topology: str) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._niswitch.NISWITCH_OPTIONS",
        NISwitchOptions("niswitch", simulate, topology),
    )

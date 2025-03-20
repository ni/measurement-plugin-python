from __future__ import annotations

import functools
from contextlib import ExitStack
from typing import Any
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service.session_management import (
    INSTRUMENT_TYPE_NI_DMM,
    MultiSessionReservation,
    SessionInitializationBehavior,
)
from tests.unit._drivers._driver_utils import (
    create_mock_session,
    create_mock_sessions,
    set_simulation_options,
)
from tests.unit._reservation_utils import create_grpc_session_infos

try:
    import nidmm
except ImportError:
    nidmm = None

pytestmark = pytest.mark.skipif(nidmm is None, reason="Requires 'nidmm' package.")

if nidmm:
    create_mock_nidmm_session = functools.partial(create_mock_session, nidmm.Session)
    create_mock_nidmm_sessions = functools.partial(create_mock_sessions, nidmm.Session)
    create_nidmm_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DMM
    )
    set_nidmm_simulation_options = functools.partial(set_simulation_options, "nidmm")


def test___single_session_info___initialize_nidmm_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_new.side_effect = [session]

    with reservation.initialize_nidmm_session(options={}) as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        nidmm.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___initialize_nidmm_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(2))
    sessions = create_mock_nidmm_sessions(3)
    session_new.side_effect = sessions

    with reservation.initialize_nidmm_sessions(options={}) as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_new.assert_any_call(
        nidmm.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )
    session_new.assert_any_call(
        nidmm.Session, resource_name="Dev1", reset_device=False, options={}, grpc_options=ANY
    )


def test___optional_args___initialize_nidmm_session___optional_args_passed(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_new.side_effect = [session]

    with reservation.initialize_nidmm_session(
        reset_device=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        nidmm.Session,
        resource_name="Dev0",
        reset_device=True,
        options={"simulate": False},
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == nidmm.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___initialize_nidmm_session___simulation_options_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidmm_simulation_options(mocker, True, "PXIe", "4081")
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_new.side_effect = [session]

    with reservation.initialize_nidmm_session():
        pass

    expected_options = {
        "simulate": True,
        "driver_setup": {"BoardType": "PXIe", "Model": "4081"},
    }
    session_new.assert_called_once_with(
        nidmm.Session,
        resource_name="Dev0",
        reset_device=False,
        options=expected_options,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___initialize_nidmm_session___optional_args_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidmm_simulation_options(mocker, True, "PXIe", "4081")
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_new.side_effect = [session]

    with reservation.initialize_nidmm_session(reset_device=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_new.assert_called_once_with(
        nidmm.Session,
        resource_name="Dev0",
        reset_device=True,
        options=expected_options,
        grpc_options=ANY,
    )


# The NI-DMM version of the get_connection(s) test cases is limited to 1 channel
# per session.
@pytest.mark.parametrize(
    "kwargs,expected_channel_name,expected_session_index",
    [
        ({"pin_name": "Pin1", "site": 0}, "0", 0),
        ({"pin_name": "Pin2", "site": 0}, "0", 1),
        ({"pin_name": "Pin1", "site": 1}, "0", 2),
        ({"pin_name": "Pin2", "site": 1}, "0", 3),
    ],
)
def test___session_created___get_nidmm_connection___connection_returned(
    kwargs: dict[str, Any],
    expected_channel_name: str,
    expected_session_index: int,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nidmm_session_infos(4)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin2", site=0, channel="0")
        grpc_session_infos[2].channel_mappings.add(pin_or_relay_name="Pin1", site=1, channel="0")
        grpc_session_infos[3].channel_mappings.add(pin_or_relay_name="Pin2", site=1, channel="0")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        sessions = create_mock_nidmm_sessions(4)
        session_new.side_effect = sessions
        session_infos = stack.enter_context(reservation.initialize_nidmm_sessions())

        connection = reservation.get_nidmm_connection(**kwargs)

        assert connection.channel_name == expected_channel_name
        assert connection.session is session_infos[expected_session_index].session


@pytest.mark.parametrize(
    "kwargs,expected_channel_names,expected_session_indices",
    [
        ({}, ["0", "0", "0", "0"], [0, 1, 2, 3]),
        ({"pin_names": "Pin1"}, ["0", "0"], [0, 2]),
        ({"pin_names": "Pin2"}, ["0", "0"], [1, 3]),
        ({"sites": 0}, ["0", "0"], [0, 1]),
        ({"sites": 1}, ["0", "0"], [2, 3]),
        ({"pin_names": ["Pin2", "Pin1"], "sites": [1, 0]}, ["0", "0", "0", "0"], [3, 2, 1, 0]),
    ],
)
def test___session_created___get_nidmm_connections___connections_returned(
    kwargs: dict[str, Any],
    expected_channel_names: list[str],
    expected_session_indices: list[int],
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nidmm_session_infos(4)
        grpc_session_infos[0].channel_mappings.add(pin_or_relay_name="Pin1", site=0, channel="0")
        grpc_session_infos[1].channel_mappings.add(pin_or_relay_name="Pin2", site=0, channel="0")
        grpc_session_infos[2].channel_mappings.add(pin_or_relay_name="Pin1", site=1, channel="0")
        grpc_session_infos[3].channel_mappings.add(pin_or_relay_name="Pin2", site=1, channel="0")
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        sessions = create_mock_nidmm_sessions(4)
        session_new.side_effect = sessions
        session_infos = stack.enter_context(reservation.initialize_nidmm_sessions())

        connections = reservation.get_nidmm_connections(**kwargs)

        assert [conn.channel_name for conn in connections] == expected_channel_names
        assert [conn.session for conn in connections] == [
            session_infos[i].session for i in expected_session_indices
        ]


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("nidmm.Session.__new__", autospec=True)

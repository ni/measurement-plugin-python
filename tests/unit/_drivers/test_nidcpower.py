import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DCPOWER,
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
    import nidcpower
except ImportError:
    nidcpower = None

pytestmark = pytest.mark.skipif(nidcpower is None, reason="Requires 'nidcpower' package.")

if nidcpower:
    create_mock_nidcpower_session = functools.partial(create_mock_session, nidcpower.Session)
    create_mock_nidcpower_sessions = functools.partial(create_mock_sessions, nidcpower.Session)
    create_nidcpower_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DCPOWER
    )
    set_nidcpower_simulation_options = functools.partial(set_simulation_options, "nidcpower")


def test___single_session_info___create_nidcpower_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidcpower_session_infos(1)
    )
    session = create_mock_nidcpower_session()
    session_new.side_effect = [session]

    with reservation.create_nidcpower_session() as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        nidcpower.Session, resource_name="Dev0", reset=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___create_nidcpower_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidcpower_session_infos(2)
    )
    sessions = create_mock_nidcpower_sessions(3)
    session_new.side_effect = sessions

    with reservation.create_nidcpower_sessions() as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_new.assert_any_call(
        nidcpower.Session, resource_name="Dev0", reset=False, options={}, grpc_options=ANY
    )
    session_new.assert_any_call(
        nidcpower.Session, resource_name="Dev1", reset=False, options={}, grpc_options=ANY
    )


def test___optional_args___create_nidcpower_session___optional_args_passed(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidcpower_session_infos(1)
    )
    session = create_mock_nidcpower_session()
    session_new.side_effect = [session]

    with reservation.create_nidcpower_session(
        reset=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        nidcpower.Session,
        resource_name="Dev0",
        reset=True,
        options={"simulate": False},
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == nidcpower.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_nidcpower_session___simulation_options_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidcpower_simulation_options(mocker, True, "PXIe", "4147")
    reservation = MultiSessionReservation(
        session_management_client, create_nidcpower_session_infos(1)
    )
    session = create_mock_nidcpower_session()
    session_new.side_effect = [session]

    with reservation.create_nidcpower_session():
        pass

    expected_options = {"simulate": True, "driver_setup": {"BoardType": "PXIe", "Model": "4147"}}
    session_new.assert_called_once_with(
        nidcpower.Session,
        resource_name="Dev0",
        reset=False,
        options=expected_options,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___create_nidcpower_session___optional_args_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidcpower_simulation_options(mocker, True, "PXIe", "4147")
    reservation = MultiSessionReservation(
        session_management_client, create_nidcpower_session_infos(1)
    )
    session = create_mock_nidcpower_session()
    session_new.side_effect = [session]

    with reservation.create_nidcpower_session(reset=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_new.assert_called_once_with(
        nidcpower.Session,
        resource_name="Dev0",
        reset=True,
        options=expected_options,
        grpc_options=ANY,
    )


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("nidcpower.Session.__new__", autospec=True)

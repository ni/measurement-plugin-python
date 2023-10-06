import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_SCOPE,
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
    import niscope
except ImportError:
    niscope = None

pytestmark = pytest.mark.skipif(niscope is None, reason="Requires 'niscope' package.")

if niscope:
    create_mock_niscope_session = functools.partial(create_mock_session, niscope.Session)
    create_mock_niscope_sessions = functools.partial(create_mock_sessions, niscope.Session)
    create_niscope_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_SCOPE
    )
    set_niscope_simulation_options = functools.partial(set_simulation_options, "niscope")


def test___single_session_info___create_niscope_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niscope_session_infos(1)
    )
    session = create_mock_niscope_session()
    session_new.side_effect = [session]

    with reservation.create_niscope_session() as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        niscope.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___create_niscope_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niscope_session_infos(2)
    )
    sessions = create_mock_niscope_sessions(3)
    session_new.side_effect = sessions

    with reservation.create_niscope_sessions() as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_new.assert_any_call(
        niscope.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )
    session_new.assert_any_call(
        niscope.Session, resource_name="Dev1", reset_device=False, options={}, grpc_options=ANY
    )


def test___optional_args___create_niscope_session___optional_args_passed(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niscope_session_infos(1)
    )
    session = create_mock_niscope_session()
    session_new.side_effect = [session]

    with reservation.create_niscope_session(
        reset_device=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        niscope.Session,
        resource_name="Dev0",
        reset_device=True,
        options={"simulate": False},
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == niscope.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_niscope_session___simulation_options_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_niscope_simulation_options(mocker, True, "PXIe", "5162 (4CH)")
    reservation = MultiSessionReservation(
        session_management_client, create_niscope_session_infos(1)
    )
    session = create_mock_niscope_session()
    session_new.side_effect = [session]

    with reservation.create_niscope_session():
        pass

    expected_options = {
        "simulate": True,
        "driver_setup": {"BoardType": "PXIe", "Model": "5162 (4CH)"},
    }
    session_new.assert_called_once_with(
        niscope.Session,
        resource_name="Dev0",
        reset_device=False,
        options=expected_options,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___create_niscope_session___optional_args_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_niscope_simulation_options(mocker, True, "PXIe", "5162 (4CH)")
    reservation = MultiSessionReservation(
        session_management_client, create_niscope_session_infos(1)
    )
    session = create_mock_niscope_session()
    session_new.side_effect = [session]

    with reservation.create_niscope_session(reset_device=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_new.assert_called_once_with(
        niscope.Session,
        resource_name="Dev0",
        reset_device=True,
        options=expected_options,
        grpc_options=ANY,
    )


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("niscope.Session.__new__", autospec=True)

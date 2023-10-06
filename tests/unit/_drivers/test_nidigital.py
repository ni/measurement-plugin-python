import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
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
    import nidigital
except ImportError:
    nidigital = None

pytestmark = pytest.mark.skipif(nidigital is None, reason="Requires 'nidigital' package.")

if nidigital:
    create_mock_nidigital_session = functools.partial(create_mock_session, nidigital.Session)
    create_mock_nidigital_sessions = functools.partial(create_mock_sessions, nidigital.Session)
    create_nidigital_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
    )
    set_nidigital_simulation_options = functools.partial(set_simulation_options, "nidigital")


def test___single_session_info___create_nidigital_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidigital_session_infos(1)
    )
    session = create_mock_nidigital_session()
    session_new.side_effect = [session]

    with reservation.create_nidigital_session() as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        nidigital.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___create_nidigital_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidigital_session_infos(2)
    )
    sessions = create_mock_nidigital_sessions(3)
    session_new.side_effect = sessions

    with reservation.create_nidigital_sessions() as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_new.assert_any_call(
        nidigital.Session, resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )
    session_new.assert_any_call(
        nidigital.Session, resource_name="Dev1", reset_device=False, options={}, grpc_options=ANY
    )


def test___optional_args___create_nidigital_session___optional_args_passed(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidigital_session_infos(1)
    )
    session = create_mock_nidigital_session()
    session_new.side_effect = [session]

    with reservation.create_nidigital_session(
        reset_device=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        nidigital.Session,
        resource_name="Dev0",
        reset_device=True,
        options={"simulate": False},
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == nidigital.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_nidigital_session___simulation_options_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidigital_simulation_options(mocker, True, "PXIe", "6570")
    reservation = MultiSessionReservation(
        session_management_client, create_nidigital_session_infos(1)
    )
    session = create_mock_nidigital_session()
    session_new.side_effect = [session]

    with reservation.create_nidigital_session():
        pass

    expected_options = {
        "simulate": True,
        "driver_setup": {"BoardType": "PXIe", "Model": "6570"},
    }
    session_new.assert_called_once_with(
        nidigital.Session,
        resource_name="Dev0",
        reset_device=False,
        options=expected_options,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___create_nidigital_session___optional_args_passed(
    mocker: MockerFixture,
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    set_nidigital_simulation_options(mocker, True, "PXIe", "6570")
    reservation = MultiSessionReservation(
        session_management_client, create_nidigital_session_infos(1)
    )
    session = create_mock_nidigital_session()
    session_new.side_effect = [session]

    with reservation.create_nidigital_session(reset_device=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_new.assert_called_once_with(
        nidigital.Session,
        resource_name="Dev0",
        reset_device=True,
        options=expected_options,
        grpc_options=ANY,
    )


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("nidigital.Session.__new__", autospec=True)

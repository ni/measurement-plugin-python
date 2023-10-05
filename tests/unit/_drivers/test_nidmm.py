import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.session_management import (
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
    # Note: this reads the Session type before it is patched.
    create_mock_nidmm_session = functools.partial(create_mock_session, nidmm.Session)
    create_mock_nidmm_sessions = functools.partial(create_mock_sessions, nidmm.Session)
    create_nidmm_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DMM
    )
    set_nidmm_simulation_options = functools.partial(set_simulation_options, "nidmm")


def test___single_session_info___create_nidmm_session___session_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_type.side_effect = [session]

    with reservation.create_nidmm_session() as session_info:
        assert session_info.session is session

    session_type.assert_called_once_with(
        resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___create_nidmm_sessions___sessions_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(2))
    sessions = create_mock_nidmm_sessions(3)
    session_type.side_effect = sessions

    with reservation.create_nidmm_sessions() as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_type.assert_any_call(
        resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )
    session_type.assert_any_call(
        resource_name="Dev1", reset_device=False, options={}, grpc_options=ANY
    )


def test___optional_args___create_nidmm_session___optional_args_passed(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_type.side_effect = [session]

    with reservation.create_nidmm_session(
        reset_device=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_type.assert_called_once_with(
        resource_name="Dev0",
        reset_device=True,
        options={"simulate": False},
        grpc_options=ANY,
    )
    assert (
        session_type.call_args.kwargs["grpc_options"].initialization_behavior
        == nidmm.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_nidmm_session___simulation_options_passed(
    mocker: MockerFixture,
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    set_nidmm_simulation_options(mocker, True, "PXIe", "4081")
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_type.side_effect = [session]

    with reservation.create_nidmm_session():
        pass

    expected_options = {
        "simulate": True,
        "driver_setup": {"BoardType": "PXIe", "Model": "4081"},
    }
    session_type.assert_called_once_with(
        resource_name="Dev0",
        reset_device=False,
        options=expected_options,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___create_nidmm_session___optional_args_passed(
    mocker: MockerFixture,
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    set_nidmm_simulation_options(mocker, True, "PXIe", "4081")
    reservation = MultiSessionReservation(session_management_client, create_nidmm_session_infos(1))
    session = create_mock_nidmm_session()
    session_type.side_effect = [session]

    with reservation.create_nidmm_session(reset_device=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_type.assert_called_once_with(
        resource_name="Dev0",
        reset_device=True,
        options=expected_options,
        grpc_options=ANY,
    )


@pytest.fixture
def session_type(mocker: MockerFixture) -> Mock:
    """A test fixture that replaces the Session class with a mock."""
    return mocker.patch("nidmm.Session", autospec=True)

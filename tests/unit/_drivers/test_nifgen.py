from typing import List
from unittest.mock import ANY, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._configuration import MIDriverOptions
from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_FGEN,
    MultiSessionReservation,
    SessionInitializationBehavior,
)

try:
    import nifgen
    from nifgen import Session as _RealSession
except ImportError:
    nifgen = None

pytestmark = pytest.mark.skipif(nifgen is None, reason="Requires 'nifgen' package.")


def test___single_session_info___create_nifgen_session___session_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, _create_grpc_session_infos(1))
    session = _create_mock_session()
    session_type.side_effect = [session]

    with reservation.create_nifgen_session() as session_info:
        assert session_info.session is session

    session_type.assert_called_once_with(
        resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )


def test___multiple_session_infos___create_nifgen_sessions___sessions_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, _create_grpc_session_infos(2))
    sessions = _create_mock_sessions(3)
    session_type.side_effect = sessions

    with reservation.create_nifgen_sessions() as session_info:
        assert session_info[0].session == sessions[0]
        assert session_info[1].session == sessions[1]

    session_type.assert_any_call(
        resource_name="Dev0", reset_device=False, options={}, grpc_options=ANY
    )
    session_type.assert_any_call(
        resource_name="Dev1", reset_device=False, options={}, grpc_options=ANY
    )


def test___optional_args___create_nifgen_session___optional_args_passed(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, _create_grpc_session_infos(1))
    session = _create_mock_session()
    session_type.side_effect = [session]

    with reservation.create_nifgen_session(
        reset_device=True,
        options={"simulate": False},
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_type.assert_called_once_with(
        resource_name="Dev0", reset_device=True, options={"simulate": False}, grpc_options=ANY
    )
    assert (
        session_type.call_args.kwargs["grpc_options"].initialization_behavior
        == nifgen.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_nifgen_session___simulation_options_passed(
    mocker: MockerFixture,
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    _set_simulation_options(mocker, True, "PXIe", "5423 (2CH)")
    reservation = MultiSessionReservation(session_management_client, _create_grpc_session_infos(1))
    session = _create_mock_session()
    session_type.side_effect = [session]

    with reservation.create_nifgen_session():
        pass

    expected_options = {
        "simulate": True,
        "driver_setup": {"BoardType": "PXIe", "Model": "5423 (2CH)"},
    }
    session_type.assert_called_once_with(
        resource_name="Dev0", reset_device=False, options=expected_options, grpc_options=ANY
    )


def test___optional_args_and_simulation_configured___create_nifgen_session___optional_args_passed(
    mocker: MockerFixture,
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    _set_simulation_options(mocker, True, "PXIe", "5423 (2CH)")
    reservation = MultiSessionReservation(session_management_client, _create_grpc_session_infos(1))
    session = _create_mock_session()
    session_type.side_effect = [session]

    with reservation.create_nifgen_session(reset_device=True, options={"simulate": False}):
        pass

    expected_options = {"simulate": False}
    session_type.assert_called_once_with(
        resource_name="Dev0", reset_device=True, options=expected_options, grpc_options=ANY
    )


@pytest.fixture
def session_type(mocker: MockerFixture) -> Mock:
    """A test fixture that replaces the Session class with a mock."""
    return mocker.patch("nifgen.Session", autospec=True)


def _create_mock_session() -> Mock:
    # Use the real Session class, not the one we patched.
    mock = create_autospec(_RealSession)
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


def _create_mock_sessions(count: int) -> List[Mock]:
    return [_create_mock_session() for _ in range(count)]


def _create_grpc_session_infos(
    session_count: int,
) -> List[session_management_service_pb2.SessionInformation]:
    return [
        session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=f"MySession{i}"),
            resource_name=f"Dev{i}",
            instrument_type_id=INSTRUMENT_TYPE_NI_FGEN,
        )
        for i in range(session_count)
    ]


def _set_simulation_options(
    mocker: MockerFixture, simulate: bool, board_type: str, model: str
) -> None:
    mocker.patch(
        "ni_measurementlink_service._drivers._nifgen.NIFGEN_OPTIONS",
        MIDriverOptions("nifgen", simulate, board_type, model),
    )

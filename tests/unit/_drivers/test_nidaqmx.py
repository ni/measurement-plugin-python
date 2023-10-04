import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DAQMX,
    MultiSessionReservation,
    SessionInitializationBehavior,
)
from tests.unit._drivers._driver_utils import create_mock_session, create_mock_sessions
from tests.unit._reservation_utils import create_grpc_session_infos

try:
    import nidaqmx
except ImportError:
    nidaqmx = None

pytestmark = pytest.mark.skipif(nidaqmx is None, reason="Requires 'nidaqmx' package.")

if nidaqmx:
    # Note: this reads the Task type before it is patched.
    create_mock_nidaqmx_task = functools.partial(create_mock_session, nidaqmx.Task)
    create_mock_nidaqmx_tasks = functools.partial(create_mock_sessions, nidaqmx.Task)
    create_nidaqmx_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DAQMX
    )


def test___single_session_info___create_nidaqmx_task___task_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(1)
    )
    task = create_mock_nidaqmx_task()
    session_type.side_effect = [task]

    with reservation.create_nidaqmx_task() as session_info:
        assert session_info.session is task

    session_type.assert_called_once_with(new_task_name="MySession0", grpc_options=ANY)


def test___multiple_session_infos___create_nidaqmx_tasks___sessions_created(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(2)
    )
    tasks = create_mock_nidaqmx_tasks(3)
    session_type.side_effect = tasks

    with reservation.create_nidaqmx_tasks() as session_info:
        assert session_info[0].session == tasks[0]
        assert session_info[1].session == tasks[1]

    session_type.assert_any_call(new_task_name="MySession0", grpc_options=ANY)
    session_type.assert_any_call(new_task_name="MySession1", grpc_options=ANY)


def test___optional_args___create_nidaqmx_task___optional_args_passed(
    session_type: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(1)
    )
    task = create_mock_nidaqmx_task()
    session_type.side_effect = [task]

    with reservation.create_nidaqmx_task(
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_type.assert_called_once_with(
        new_task_name="MySession0",
        grpc_options=ANY,
    )
    assert (
        session_type.call_args.kwargs["grpc_options"].initialization_behavior
        == nidaqmx.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


@pytest.fixture
def session_type(mocker: MockerFixture) -> Mock:
    """A test fixture that replaces the Session class with a mock."""
    return mocker.patch("nidaqmx.Task", autospec=True)

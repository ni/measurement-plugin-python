from __future__ import annotations

import functools
from contextlib import ExitStack
from typing import Any
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service.session_management import (
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
    create_mock_nidaqmx_task = functools.partial(create_mock_session, nidaqmx.Task)
    create_mock_nidaqmx_tasks = functools.partial(create_mock_sessions, nidaqmx.Task)
    create_nidaqmx_session_infos = functools.partial(
        create_grpc_session_infos, INSTRUMENT_TYPE_NI_DAQMX
    )


def test___single_session_info___create_nidaqmx_task___task_created(
    task_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(1)
    )
    task = create_mock_nidaqmx_task()
    task_new.side_effect = [task]

    with reservation.create_nidaqmx_task() as session_info:
        assert session_info.session is task

    task_new.assert_called_once_with(nidaqmx.Task, new_task_name="MySession0", grpc_options=ANY)


def test___multiple_session_infos___create_nidaqmx_tasks___tasks_created(
    task_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(2)
    )
    tasks = create_mock_nidaqmx_tasks(2)
    task_new.side_effect = tasks

    with reservation.create_nidaqmx_tasks() as session_info:
        assert session_info[0].session == tasks[0]
        assert session_info[1].session == tasks[1]

    task_new.assert_any_call(nidaqmx.Task, new_task_name="MySession0", grpc_options=ANY)
    task_new.assert_any_call(nidaqmx.Task, new_task_name="MySession1", grpc_options=ANY)


def test___optional_args___create_nidaqmx_task___optional_args_passed(
    task_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_nidaqmx_session_infos(1)
    )
    task = create_mock_nidaqmx_task()
    task_new.side_effect = [task]

    with reservation.create_nidaqmx_task(
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    task_new.assert_called_once_with(
        nidaqmx.Task,
        new_task_name="MySession0",
        grpc_options=ANY,
    )
    assert (
        task_new.call_args.kwargs["grpc_options"].initialization_behavior
        == nidaqmx.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


# The NI-DAQmx version of the get_connection(s) test cases uses fully
# qualified channel names.
@pytest.mark.parametrize(
    "kwargs,expected_channel_name,expected_session_index",
    [
        ({"pin_name": "Pin1", "site": 0}, "Dev1/ai0", 0),
        ({"pin_name": "Pin2", "site": 0}, "Dev1/ai1", 0),
        ({"pin_name": "Pin1", "site": 1}, "Dev2/ai2", 0),
        ({"pin_name": "Pin2", "site": 1}, "Dev3/ai0", 1),
    ],
)
def test___task_created___get_nidaqmx_connection___connection_returned(
    kwargs: dict[str, Any],
    expected_channel_name: str,
    expected_session_index: int,
    task_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nidaqmx_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1", site=0, channel="Dev1/ai0"
        )
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin2", site=0, channel="Dev1/ai1"
        )
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1", site=1, channel="Dev2/ai2"
        )
        grpc_session_infos[1].channel_mappings.add(
            pin_or_relay_name="Pin2", site=1, channel="Dev3/ai0"
        )
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        tasks = create_mock_nidaqmx_tasks(2)
        task_new.side_effect = tasks
        session_infos = stack.enter_context(reservation.create_nidaqmx_tasks())

        connection = reservation.get_nidaqmx_connection(**kwargs)

        assert connection.channel_name == expected_channel_name
        assert connection.session is session_infos[expected_session_index].session


@pytest.mark.parametrize(
    "kwargs,expected_channel_names,expected_session_indices",
    [
        ({}, ["Dev1/ai0", "Dev1/ai1", "Dev2/ai2", "Dev3/ai0"], [0, 0, 0, 1]),
        ({"pin_names": "Pin1"}, ["Dev1/ai0", "Dev2/ai2"], [0, 0]),
        ({"pin_names": "Pin2"}, ["Dev1/ai1", "Dev3/ai0"], [0, 1]),
        ({"sites": 0}, ["Dev1/ai0", "Dev1/ai1"], [0, 0]),
        ({"sites": 1}, ["Dev2/ai2", "Dev3/ai0"], [0, 1]),
        (
            {"pin_names": ["Pin2", "Pin1"], "sites": [1, 0]},
            ["Dev3/ai0", "Dev2/ai2", "Dev1/ai1", "Dev1/ai0"],
            [1, 0, 0, 0],
        ),
    ],
)
def test___task_created___get_nidaqmx_connections___connections_returned(
    kwargs: dict[str, Any],
    expected_channel_names: list[str],
    expected_session_indices: list[int],
    task_new: Mock,
    session_management_client: Mock,
) -> None:
    with ExitStack() as stack:
        grpc_session_infos = create_nidaqmx_session_infos(2)
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1", site=0, channel="Dev1/ai0"
        )
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin2", site=0, channel="Dev1/ai1"
        )
        grpc_session_infos[0].channel_mappings.add(
            pin_or_relay_name="Pin1", site=1, channel="Dev2/ai2"
        )
        grpc_session_infos[1].channel_mappings.add(
            pin_or_relay_name="Pin2", site=1, channel="Dev3/ai0"
        )
        reservation = MultiSessionReservation(session_management_client, grpc_session_infos)
        tasks = create_mock_nidaqmx_tasks(2)
        task_new.side_effect = tasks
        session_infos = stack.enter_context(reservation.create_nidaqmx_tasks())

        connections = reservation.get_nidaqmx_connections(**kwargs)

        assert [conn.channel_name for conn in connections] == expected_channel_names
        assert [conn.session for conn in connections] == [
            session_infos[i].session for i in expected_session_indices
        ]


@pytest.fixture
def task_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Task class's __new__ method."""
    return mocker.patch("nidaqmx.Task.__new__", autospec=True)

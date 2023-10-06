import functools
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._configuration import NISwitchOptions
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    MultiSessionReservation,
    SessionInitializationBehavior,
)
from tests.unit._drivers._driver_utils import (
    create_mock_session,
    create_mock_sessions,
)
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


def test___single_session_info___create_niswitch_session___session_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.create_niswitch_session() as session_info:
        assert session_info.session is session

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="Dev0",
        topology="Configured Topology",
        simulate=False,
        reset_device=False,
        grpc_options=ANY,
    )


def test___multiple_session_infos___create_niswitch_sessions___sessions_created(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(2)
    )
    sessions = create_mock_niswitch_sessions(3)
    session_new.side_effect = sessions

    with reservation.create_niswitch_sessions() as session_info:
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


def test___optional_args___create_niswitch_session___optional_args_passed(
    session_new: Mock,
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, create_niswitch_session_infos(1)
    )
    session = create_mock_niswitch_session()
    session_new.side_effect = [session]

    with reservation.create_niswitch_session(
        topology="2567/Independent",
        simulate=True,
        reset_device=True,
        initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ):
        pass

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="Dev0",
        topology="2567/Independent",
        simulate=True,
        reset_device=True,
        grpc_options=ANY,
    )
    assert (
        session_new.call_args.kwargs["grpc_options"].initialization_behavior
        == niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___simulation_configured___create_niswitch_session___simulation_options_passed(
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

    with reservation.create_niswitch_session():
        pass

    session_new.assert_called_once_with(
        niswitch.Session,
        resource_name="Dev0",
        topology="2567/Independent",
        simulate=True,
        reset_device=False,
        grpc_options=ANY,
    )


def test___optional_args_and_simulation_configured___create_niswitch_session___optional_args_passed(
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

    with reservation.create_niswitch_session(
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


@pytest.fixture
def session_new(mocker: MockerFixture) -> Mock:
    """A test fixture that patches the Session class's __new__ method."""
    return mocker.patch("niswitch.Session.__new__", autospec=True)


def _set_niswitch_simulation_options(mocker: MockerFixture, simulate: bool, topology: str) -> None:
    mocker.patch(
        "ni_measurementlink_service._drivers._niswitch.NISWITCH_OPTIONS",
        NISwitchOptions("niswitch", simulate, topology),
    )

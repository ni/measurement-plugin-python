import functools
from unittest.mock import Mock

import pytest

from ni_measurementlink_service.session_management import (
    MultiSessionReservation,
    SessionInformation,
)
from tests.unit._reservation_utils import create_grpc_session_infos
from tests.utilities import fake_driver

create_nifake_session_infos = functools.partial(create_grpc_session_infos, "nifake")
create_nifoo_session_infos = functools.partial(create_grpc_session_infos, "nifoo")


def test___single_session_info___create_session___session_info_yielded(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.create_session(_construct_session, "nifake") as session_info:
        assert session_info.session_name == "MySession0"
        assert session_info.resource_name == "Dev0"
        assert session_info.instrument_type_id == "nifake"


def test___single_session_info___create_session___session_created(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.create_session(_construct_session, "nifake") as session_info:
        assert isinstance(session_info.session, fake_driver.Session)
        assert session_info.session.resource_name == "Dev0"


def test___single_session_info___create_session___session_lifetime_tracked(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.create_session(_construct_session, "nifake") as session_info:
        assert reservation._session_cache["MySession0"] is session_info.session
        assert not session_info.session.is_closed

    assert len(reservation._session_cache) == 0
    assert session_info.session.is_closed


def test___empty_instrument_type_id___create_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_session(_construct_session, ""):
            pass

    assert "This method requires an instrument type ID." in exc_info.value.args[0]


def test___no_session_infos___create_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(0))

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_session(_construct_session, "nifake"):
            pass

    assert "No reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___multi_session_infos___create_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(2))

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_session(_construct_session, "nifake"):
            pass

    assert "Too many reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___session_already_exists___create_session___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(1))

    with reservation.create_session(_construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.create_session(_construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___create_session___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifoo_session_infos(2)
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.create_session(
        _construct_session, "nifoo"
    ) as nifoo_info, reservation.create_session(_construct_session, "nibar") as nibar_info:
        assert nifoo_info.session_name == "MySession0"
        assert nifoo_info.instrument_type_id == "nifoo"
        assert nibar_info.session_name == "MySession1"
        assert nibar_info.instrument_type_id == "nibar"


def test___multi_session_infos___create_sessions___session_infos_yielded(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.create_sessions(_construct_session, "nifake") as session_infos:
        assert [info.session_name for info in session_infos] == [
            "MySession0",
            "MySession1",
            "MySession2",
        ]
        assert [info.resource_name for info in session_infos] == ["Dev0", "Dev1", "Dev2"]
        assert [info.instrument_type_id for info in session_infos] == ["nifake", "nifake", "nifake"]


def test___multi_session_infos___create_sessions___sessions_created(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.create_sessions(_construct_session, "nifake") as session_infos:
        assert all([isinstance(info.session, fake_driver.Session) for info in session_infos])
        assert [info.session.resource_name for info in session_infos] == ["Dev0", "Dev1", "Dev2"]


def test___multi_session_infos___create_sessions___session_lifetime_tracked(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.create_sessions(_construct_session, "nifake") as session_infos:
        assert reservation._session_cache["MySession0"] is session_infos[0].session
        assert reservation._session_cache["MySession1"] is session_infos[1].session
        assert reservation._session_cache["MySession2"] is session_infos[2].session
        assert all([not info.session.is_closed for info in session_infos])

    assert len(reservation._session_cache) == 0
    assert all([info.session.is_closed for info in session_infos])


def test___empty_instrument_type_id___create_sessions___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_sessions(_construct_session, ""):
            pass

    assert "This method requires an instrument type ID." in exc_info.value.args[0]


def test___no_session_infos___create_sessions___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, [])

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_sessions(_construct_session, "nifake"):
            pass

    assert "No reserved sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___session_already_exists___create_sessions___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(session_management_client, create_nifake_session_infos(3))

    with reservation.create_sessions(_construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.create_sessions(_construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___create_sessions___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = create_nifoo_session_infos(3)
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.create_sessions(
        _construct_session, "nifoo"
    ) as nifoo_infos, reservation.create_sessions(_construct_session, "nibar") as nibar_infos:
        assert [info.session_name for info in nifoo_infos] == ["MySession0", "MySession2"]
        assert [info.instrument_type_id for info in nifoo_infos] == ["nifoo", "nifoo"]
        assert [info.session_name for info in nibar_infos] == ["MySession1"]
        assert [info.instrument_type_id for info in nibar_infos] == ["nibar"]


def _construct_session(session_info: SessionInformation) -> fake_driver.Session:
    return fake_driver.Session(session_info.resource_name)

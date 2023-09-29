from typing import List
from unittest.mock import Mock

import pytest

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.session_management import (
    MultiSessionReservation,
    SessionInformation,
)
from tests.utilities import fake_driver


def test___single_session_info___create_session___yields_session_info(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(1, "nifake")
    )

    with reservation.create_session(_construct_session, "nifake") as (
        session_info,
        session,
    ):
        assert session_info.session_name == "MySession0"
        assert session_info.resource_name == "Dev0"
        assert session_info.instrument_type_id == "nifake"


def test___single_session_info___create_session___session_created_and_closed(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(1, "nifake")
    )

    with reservation.create_session(_construct_session, "nifake") as (
        session_info,
        session,
    ):
        assert isinstance(session, fake_driver.Session)
        assert session.resource_name == "Dev0"
        assert not session.is_closed

    assert session.is_closed


def test___single_session_info___create_session___session_cached(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(1, "nifake")
    )

    with reservation.create_session(_construct_session, "nifake") as (
        session_info,
        session,
    ):
        assert reservation._session_cache["MySession0"] is session

    assert len(reservation._session_cache) == 0


def test___no_session_infos___create_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(0, "nifake")
    )

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_session(_construct_session, "nifake"):
            pass

    assert "No sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___multi_session_infos___create_session___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(2, "nifake")
    )

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_session(_construct_session, "nifake"):
            pass

    assert "Too many sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___session_already_exists___create_session___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(1, "nifake")
    )

    with reservation.create_session(_construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.create_session(_construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___create_session___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos(2, "nifoo")
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.create_session(_construct_session, "nifoo") as (
        nifoo_info,
        nifoo_session,
    ), reservation.create_session(_construct_session, "nibar") as (nibar_info, nibar_session):
        assert nifoo_info.session_name == "MySession0"
        assert nifoo_info.instrument_type_id == "nifoo"
        assert nibar_info.session_name == "MySession1"
        assert nibar_info.instrument_type_id == "nibar"


def test___multi_session_infos___create_sessions___yields_session_infos(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(3, "nifake")
    )

    with reservation.create_sessions(_construct_session, "nifake") as session_tuples:
        assert [t[0].session_name for t in session_tuples] == [
            "MySession0",
            "MySession1",
            "MySession2",
        ]
        assert [t[0].resource_name for t in session_tuples] == ["Dev0", "Dev1", "Dev2"]
        assert [t[0].instrument_type_id for t in session_tuples] == ["nifake", "nifake", "nifake"]


def test___multi_session_infos___create_sessions___sessions_created_and_closed(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(1, "nifake")
    )

    with reservation.create_sessions(_construct_session, "nifake") as session_tuples:
        assert all([isinstance(t[1], fake_driver.Session) for t in session_tuples])
        assert [t[1].resource_name for t in session_tuples]
        assert all([not t[1].is_closed for t in session_tuples])

    assert all([t[1].is_closed for t in session_tuples])


def test___multi_session_infos___create_sessions___sessions_cached(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(3, "nifake")
    )

    with reservation.create_sessions(_construct_session, "nifake") as session_tuples:
        assert reservation._session_cache["MySession0"] is session_tuples[0][1]
        assert reservation._session_cache["MySession1"] is session_tuples[1][1]
        assert reservation._session_cache["MySession2"] is session_tuples[2][1]

    assert len(reservation._session_cache) == 0


def test___no_session_infos___create_sessions___value_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(0, "nifake")
    )

    with pytest.raises(ValueError) as exc_info:
        with reservation.create_sessions(_construct_session, "nifake"):
            pass

    assert "No sessions matched instrument type ID 'nifake'." in exc_info.value.args[0]


def test___session_already_exists___create_sessions___runtime_error_raised(
    session_management_client: Mock,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(3, "nifake")
    )

    with reservation.create_sessions(_construct_session, "nifake"):
        with pytest.raises(RuntimeError) as exc_info:
            with reservation.create_sessions(_construct_session, "nifake"):
                pass

    assert "Session 'MySession0' already exists." in exc_info.value.args[0]


def test___heterogenous_session_infos___create_sessions___grouped_by_instrument_type(
    session_management_client: Mock,
) -> None:
    grpc_session_infos = _create_grpc_session_infos(3, "nifoo")
    grpc_session_infos[1].instrument_type_id = "nibar"
    reservation = MultiSessionReservation(session_management_client, grpc_session_infos)

    with reservation.create_sessions(
        _construct_session, "nifoo"
    ) as nifoo_tuples, reservation.create_sessions(_construct_session, "nibar") as nibar_tuples:
        assert [t[0].session_name for t in nifoo_tuples] == ["MySession0", "MySession2"]
        assert [t[0].instrument_type_id for t in nifoo_tuples] == ["nifoo", "nifoo"]
        assert [t[0].session_name for t in nibar_tuples] == ["MySession1"]
        assert [t[0].instrument_type_id for t in nibar_tuples] == ["nibar"]


def _construct_session(session_info: SessionInformation) -> fake_driver.Session:
    return fake_driver.Session(session_info.resource_name)


def _create_grpc_session_infos(
    session_count: int,
    instrument_type_id: str,
) -> List[session_management_service_pb2.SessionInformation]:
    return [
        session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=f"MySession{i}"),
            resource_name=f"Dev{i}",
            instrument_type_id=instrument_type_id,
        )
        for i in range(session_count)
    ]

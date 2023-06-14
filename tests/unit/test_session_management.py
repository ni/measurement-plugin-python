from typing import List, cast
from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1.session_management_service_pb2_grpc import (
    SessionManagementServiceStub,
)
from ni_measurementlink_service.session_management import (
    Client,
    PinMapContext,
    Reservation,
    SessionInformation,
)


def test___reserve_sessions___sends_request(client: Client, stub: Mock) -> None:
    stub.ReserveSessions.return_value = session_management_service_pb2.ReserveSessionsResponse()

    _ = client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    stub.ReserveSessions.assert_called_once()
    (request,) = stub.ReserveSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.pin_or_relay_names == ["Pin1", "Pin2"]
    assert request.instrument_type_id == "MyInstrumentType"
    assert request.timeout_in_milliseconds == 123456


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___reserve_sessions___returns_session_infos(
    client: Client, stub: Mock, session_count: int
) -> None:
    stub.ReserveSessions.return_value = session_management_service_pb2.ReserveSessionsResponse(
        sessions=_create_grpc_session_infos(session_count)
    )

    reservation = client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    assert len(reservation.session_info) == session_count
    assert [s.session_name for s in reservation.session_info] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___unreserve___sends_request(
    client: Client, stub: Mock, session_count: int
) -> None:
    reservation = Reservation(client, _create_grpc_session_infos(session_count))
    stub.UnreserveSessions.return_value = session_management_service_pb2.UnreserveSessionsResponse()

    reservation.unreserve()

    stub.UnreserveSessions.assert_called_once()
    (request,) = stub.UnreserveSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___exit_reservation___sends_request(
    client: Client, stub: Mock, session_count: int
) -> None:
    reservation = Reservation(client, _create_grpc_session_infos(session_count))
    stub.UnreserveSessions.return_value = session_management_service_pb2.UnreserveSessionsResponse()

    with reservation:
        pass

    stub.UnreserveSessions.assert_called_once()
    (request,) = stub.UnreserveSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___register_sessions___sends_request(
    client: Client, stub: Mock, session_count: int
) -> None:
    stub.RegisterSessions.return_value = session_management_service_pb2.RegisterSessionsResponse()

    client.register_sessions(_create_session_infos(session_count))

    stub.RegisterSessions.assert_called_once()
    (request,) = stub.RegisterSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___unregister_sessions___sends_request(
    client: Client, stub: Mock, session_count: int
) -> None:
    stub.UnregisterSessions.return_value = (
        session_management_service_pb2.UnregisterSessionsResponse()
    )

    client.unregister_sessions(_create_session_infos(session_count))

    stub.UnregisterSessions.assert_called_once()
    (request,) = stub.UnregisterSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


def test___reserve_all_registered_sessions___sends_request(client: Client, stub: Mock) -> None:
    stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    _ = client.reserve_all_registered_sessions(
        instrument_type_id="MyInstrumentType", timeout=123.456
    )

    stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = stub.ReserveAllRegisteredSessions.call_args.args
    assert request.instrument_type_id == "MyInstrumentType"
    assert request.timeout_in_milliseconds == 123456


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___reserve_all_registered_sessions___returns_session_infos(
    client: Client, stub: Mock, session_count: int
) -> None:
    stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse(
            sessions=_create_grpc_session_infos(session_count)
        )
    )

    reservation = client.reserve_all_registered_sessions(
        instrument_type_id="MyInstrumentType", timeout=123.456
    )

    assert len(reservation.session_info) == session_count
    assert [s.session_name for s in reservation.session_info] == [
        f"MySession{i}" for i in range(session_count)
    ]


def _create_session_infos(session_count: int) -> List[SessionInformation]:
    return [
        SessionInformation(f"MySession{i}", "", "", "", False, []) for i in range(session_count)
    ]


def _create_grpc_session_infos(
    session_count: int,
) -> List[session_management_service_pb2.SessionInformation]:
    return [
        session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=f"MySession{i}")
        )
        for i in range(session_count)
    ]


@pytest.fixture
def grpc_channel(mocker: MockerFixture) -> Mock:
    """Create a mock grpc.Channel."""
    return mocker.create_autospec(grpc.Channel)


@pytest.fixture
def stub(mocker: MockerFixture) -> Mock:
    """Create a mock SessionManagementServiceStub."""
    stub = mocker.create_autospec(SessionManagementServiceStub)
    stub.ReserveSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnreserveSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.RegisterSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnregisterSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.ReserveAllRegisteredSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    return stub


@pytest.fixture
def client(grpc_channel: Mock, stub: Mock) -> Client:
    """Create a Client with a mock SessionManagementServiceStub."""
    client = Client(grpc_channel=cast(grpc.Channel, grpc_channel))
    client._client = cast(SessionManagementServiceStub, stub)
    return client

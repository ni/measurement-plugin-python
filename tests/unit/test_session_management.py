from typing import List, cast
from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1.session_management_service_pb2_grpc import (
    SessionManagementServiceStub,
)
from ni_measurementlink_service.session_management import (
    MultiSessionReservation,
    PinMapContext,
    SessionInformation,
    SessionManagementClient,
    SingleSessionReservation,
)


def test___all_optional_args___reserve_session___sends_request_with_args(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.pin_or_relay_names == ["Pin1", "Pin2"]
    assert request.instrument_type_id == "MyInstrumentType"
    assert request.timeout_in_milliseconds == 123456


def test___no_optional_args___reserve_session___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_or_relay_names == []
    assert request.instrument_type_id == ""
    assert request.timeout_in_milliseconds == 0.0


def test___single_pin___reserve_session___sends_request_with_single_pin(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names="Pin1",
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_or_relay_names == ["Pin1"]


def test___single_session___reserve_session___returns_single_session_info(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    reservation = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    assert isinstance(reservation, SingleSessionReservation)
    assert reservation.session_info.session_name == "MySession0"


def test___no_sessions___reserve_session___raises_no_sessions_value_error(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    with pytest.raises(ValueError, match="No sessions reserved."):
        _ = session_management_client.reserve_session(
            PinMapContext("MyPinMap", [0, 1]),
            pin_or_relay_names=["Pin1", "Pin2"],
            instrument_type_id="MyInstrumentType",
            timeout=123.456,
        )


def test___too_many_sessions___reserve_session___raises_too_many_sessions_value_error(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(2)
        )
    )

    with pytest.raises(ValueError, match="Too many sessions reserved."):
        _ = session_management_client.reserve_session(
            PinMapContext("MyPinMap", [0, 1]),
            pin_or_relay_names=["Pin1", "Pin2"],
            instrument_type_id="MyInstrumentType",
            timeout=123.456,
        )


def test___all_optional_args___reserve_sessions___sends_request_with_args(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    _ = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.pin_or_relay_names == ["Pin1", "Pin2"]
    assert request.instrument_type_id == "MyInstrumentType"
    assert request.timeout_in_milliseconds == 123456


def test___no_optional_args___reserve_sessions___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    _ = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_or_relay_names == []
    assert request.instrument_type_id == ""
    assert request.timeout_in_milliseconds == 0.0


def test___single_pin___reserve_sessions___sends_request_with_single_pin(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    _ = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names="Pin1",
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.pin_or_relay_names == ["Pin1"]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___reserve_sessions___returns_multiple_session_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(session_count)
        )
    )

    reservation = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    assert isinstance(reservation, MultiSessionReservation)
    assert len(reservation.session_info) == session_count
    assert [s.session_name for s in reservation.session_info] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___unreserve___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(session_count)
    )
    session_management_stub.UnreserveSessions.return_value = (
        session_management_service_pb2.UnreserveSessionsResponse()
    )

    reservation.unreserve()

    session_management_stub.UnreserveSessions.assert_called_once()
    (request,) = session_management_stub.UnreserveSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___exit_reservation___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    reservation = MultiSessionReservation(
        session_management_client, _create_grpc_session_infos(session_count)
    )
    session_management_stub.UnreserveSessions.return_value = (
        session_management_service_pb2.UnreserveSessionsResponse()
    )

    with reservation:
        pass

    session_management_stub.UnreserveSessions.assert_called_once()
    (request,) = session_management_stub.UnreserveSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___register_sessions___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    session_management_stub.RegisterSessions.return_value = (
        session_management_service_pb2.RegisterSessionsResponse()
    )

    session_management_client.register_sessions(_create_session_infos(session_count))

    session_management_stub.RegisterSessions.assert_called_once()
    (request,) = session_management_stub.RegisterSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___unregister_sessions___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    session_management_stub.UnregisterSessions.return_value = (
        session_management_service_pb2.UnregisterSessionsResponse()
    )

    session_management_client.unregister_sessions(_create_session_infos(session_count))

    session_management_stub.UnregisterSessions.assert_called_once()
    (request,) = session_management_stub.UnregisterSessions.call_args.args
    assert len(request.sessions) == session_count
    assert [s.session.name for s in request.sessions] == [
        f"MySession{i}" for i in range(session_count)
    ]


def test___reserve_all_registered_sessions___sends_request(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    _ = session_management_client.reserve_all_registered_sessions(
        instrument_type_id="MyInstrumentType", timeout=123.456
    )

    session_management_stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = session_management_stub.ReserveAllRegisteredSessions.call_args.args
    assert request.instrument_type_id == "MyInstrumentType"
    assert request.timeout_in_milliseconds == 123456


@pytest.mark.parametrize("session_count", [0, 1, 2])
def test___varying_session_count___reserve_all_registered_sessions___returns_session_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    session_count: int,
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse(
            sessions=_create_grpc_session_infos(session_count)
        )
    )

    reservation = session_management_client.reserve_all_registered_sessions(
        instrument_type_id="MyInstrumentType", timeout=123.456
    )

    assert len(reservation.session_info) == session_count
    assert [s.session_name for s in reservation.session_info] == [
        f"MySession{i}" for i in range(session_count)
    ]


def test___use_reservation_type___reports_deprecated_warning_and_aliases_to_multi_session_reservation(
    session_management_client: SessionManagementClient,
) -> None:
    with pytest.deprecated_call():
        from ni_measurementlink_service.session_management import Reservation

        reservation = Reservation(session_management_client, _create_grpc_session_infos(3))

    assert isinstance(reservation, MultiSessionReservation)


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
def session_management_client(
    discovery_client: Mock,
    grpc_channel_pool: Mock,
    mocker: MockerFixture,
    session_management_stub: Mock,
) -> SessionManagementClient:
    """Create a Client with a mock SessionManagementServiceStub."""
    mocker.patch(
        "ni_measurementlink_service.session_management.SessionManagementClient._get_stub",
        return_value=session_management_stub,
    )
    client = SessionManagementClient(
        discovery_client=cast(DiscoveryClient, discovery_client),
        grpc_channel_pool=cast(GrpcChannelPool, grpc_channel_pool),
    )
    return client


@pytest.fixture
def session_management_stub(mocker: MockerFixture) -> Mock:
    """Create a mock SessionManagementServiceStub."""
    stub = mocker.create_autospec(SessionManagementServiceStub)
    stub.ReserveSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnreserveSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.RegisterSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnregisterSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.ReserveAllRegisteredSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    return stub

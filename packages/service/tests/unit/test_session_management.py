from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._internal.stubs import session_pb2
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.sessionmanagement.v1.session_management_service_pb2_grpc import (
    SessionManagementServiceStub,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.session_management import (
    MultiplexerSessionInformation,
    MultiSessionReservation,
    PinMapContext,
    SessionInformation,
    SessionManagementClient,
    SingleSessionReservation,
    TypedSessionInformation,
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


def test___explicit_none___reserve_session___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=None,
        instrument_type_id=None,
        timeout=None,
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


@pytest.mark.parametrize("timeout", [-1, -1.0])
def test___infinite_timeout___reserve_session___sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    timeout: float,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]), timeout=timeout
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


def test___negative_timeout___reserve_session___warns_and_sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    with pytest.warns(RuntimeWarning):
        _ = session_management_client.reserve_session(PinMapContext("MyPinMap", [0, 1]), timeout=-2)

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


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


def test___all_optional_args___reserve_session___args_passed_to_reservation(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    reservation = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [1, 0, 3, 2]),
        pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    assert list(reservation._reserved_pin_or_relay_names) == ["Pin3", "Pin1", "Pin4", "Pin2"]
    assert list(reservation._reserved_sites) == [1, 0, 3, 2]


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


def test___explicit_none___reserve_sessions___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    _ = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=None,
        instrument_type_id=None,
        timeout=None,
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


@pytest.mark.parametrize("timeout", [-1, -1.0])
def test___infinite_timeout___reserve_sessions___sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    timeout: float,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    _ = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]), timeout=timeout
    )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


def test___negative_timeout___reserve_sessions___warns_and_sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1)
        )
    )

    with pytest.warns(RuntimeWarning):
        _ = session_management_client.reserve_sessions(
            PinMapContext("MyPinMap", [0, 1]), timeout=-2
        )

    session_management_stub.ReserveSessions.assert_called_once()
    (request,) = session_management_stub.ReserveSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


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


def test___all_optional_args___reserve_sessions___args_passed_to_reservation(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse()
    )

    reservation = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [1, 0, 3, 2]),
        pin_or_relay_names=["Pin3", "Pin1", "Pin4", "Pin2"],
        instrument_type_id="MyInstrumentType",
        timeout=123.456,
    )

    assert list(reservation._reserved_pin_or_relay_names) == ["Pin3", "Pin1", "Pin4", "Pin2"]
    assert list(reservation._reserved_sites) == [1, 0, 3, 2]


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


def test___all_optional_args___reserve_all_registered_sessions___sends_request_with_args(
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


def test___no_optional_args___reserve_all_registered_sessions___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    _ = session_management_client.reserve_all_registered_sessions()

    session_management_stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = session_management_stub.ReserveAllRegisteredSessions.call_args.args
    assert request.instrument_type_id == ""
    assert request.timeout_in_milliseconds == 10000


def test___explicit_none___reserve_all_registered_sessions___sends_request_with_defaults(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    _ = session_management_client.reserve_all_registered_sessions(
        instrument_type_id=None, timeout=None
    )

    session_management_stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = session_management_stub.ReserveAllRegisteredSessions.call_args.args
    assert request.instrument_type_id == ""
    assert request.timeout_in_milliseconds == 0


@pytest.mark.parametrize("timeout", [-1, -1.0])
def test___infinite_timeout___reserve_all_registered_sessions___sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    timeout: float,
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    _ = session_management_client.reserve_all_registered_sessions(timeout=timeout)

    session_management_stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = session_management_stub.ReserveAllRegisteredSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


def test___negative_timeout___reserve_all_registered_sessions___warns_and_sends_request_with_infinite_timeout(
    session_management_client: SessionManagementClient, session_management_stub: Mock
) -> None:
    session_management_stub.ReserveAllRegisteredSessions.return_value = (
        session_management_service_pb2.ReserveAllRegisteredSessionsResponse()
    )

    with pytest.warns(RuntimeWarning):
        _ = session_management_client.reserve_all_registered_sessions(timeout=-2)

    session_management_stub.ReserveAllRegisteredSessions.assert_called_once()
    (request,) = session_management_stub.ReserveAllRegisteredSessions.call_args.args
    assert request.timeout_in_milliseconds == -1


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
        from ni_measurement_plugin_sdk_service.session_management import Reservation

        reservation = Reservation(session_management_client, _create_grpc_session_infos(3))

    assert isinstance(reservation, MultiSessionReservation)


def test___session_information___type_check___implements_typed_session_information_object() -> None:
    # This is a type-checking test. It does nothing at run time.
    def f(typed_session_info: TypedSessionInformation[object]) -> None:
        pass

    f(SessionInformation("MySession", "Dev1", "0", "niDCPower", False, []))


@pytest.mark.parametrize("multiplexer_session_count", [1, 2, 3])
def test___single_session_with_varying_multiplexer_count___reserve_session___returns_session_info_and_multiplexer_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count),
        )
    )

    reservation = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0]),
        pin_or_relay_names=["Pin1", "Pin2", "Pin3"],
    )

    assert isinstance(reservation, SingleSessionReservation)
    assert reservation.session_info.session_name == "MySession0"
    assert [info.session_name for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]
    assert [info.multiplexer_type_id for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexerType{i}" for i in range(multiplexer_session_count)
    ]


@pytest.mark.parametrize("multiplexer_session_count", [1, 2, 3])
def test___multiple_sessions_with_varying_multiplexer_count___reserve_sessions___returns_session_infos_and_multiplexer_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(2),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count),
        )
    )

    reservation = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0]),
        pin_or_relay_names=["Pin1", "Pin2", "Pin3"],
    )

    assert isinstance(reservation, MultiSessionReservation)
    assert [info.session_name for info in reservation.session_info] == [
        f"MySession{i}" for i in range(2)
    ]
    assert [info.session_name for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]
    assert [info.multiplexer_type_id for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexerType{i}" for i in range(multiplexer_session_count)
    ]


@pytest.mark.parametrize("multiplexer_session_count", [1, 2])
def test___single_session_with_shared_pins_and_varying_multiplexer_count___reserve_session___returns_session_and_multiplexer_infos_for_all_sites(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count),
        )
    )

    reservation = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1"],
    )

    assert isinstance(reservation, SingleSessionReservation)
    assert list(reservation._reserved_sites) == [0, 1]
    assert [info.session_name for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]
    assert [info.multiplexer_type_id for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexerType{i}" for i in range(multiplexer_session_count)
    ]


@pytest.mark.parametrize("multiplexer_session_count", [1, 2])
def test___multiple_sessions_with_shared_pins_and_varying_multiplexer_count___reserve_sessions___returns_session_and_multiplexer_infos_for_all_sites(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(2),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count),
        )
    )

    reservation = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0, 1]),
        pin_or_relay_names=["Pin1"],
    )

    assert isinstance(reservation, MultiSessionReservation)
    assert list(reservation._reserved_sites) == [0, 1]
    assert [info.session_name for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]
    assert [info.multiplexer_type_id for info in reservation.multiplexer_session_info] == [
        f"MyMultiplexerType{i}" for i in range(multiplexer_session_count)
    ]


def test___single_session_without_multiplexer___get_multiplexer_session_info___returns_empty_list(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(1),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(0),
        )
    )
    reservation = session_management_client.reserve_session(
        PinMapContext("MyPinMap", [0]),
        pin_or_relay_names=["Pin1"],
    )

    multiplexer_session_info = reservation.multiplexer_session_info

    assert isinstance(reservation, SingleSessionReservation)
    assert len(multiplexer_session_info) == 0


def test___multiple_sessions_without_multiplexer___get_multiplexer_session_info___returns_empty_list(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.ReserveSessions.return_value = (
        session_management_service_pb2.ReserveSessionsResponse(
            sessions=_create_grpc_session_infos(2),
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(0),
        )
    )
    reservation = session_management_client.reserve_sessions(
        PinMapContext("MyPinMap", [0]),
        pin_or_relay_names=["Pin1", "Pin2"],
    )

    multiplexer_session_info = reservation.multiplexer_session_info

    assert isinstance(reservation, MultiSessionReservation)
    assert len(multiplexer_session_info) == 0


@pytest.mark.parametrize("multiplexer_session_count", [0, 1, 2])
def test___varying_multiplexer_session_count___register_multiplexer_sessions___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.RegisterMultiplexerSessions.return_value = (
        session_management_service_pb2.RegisterMultiplexerSessionsResponse()
    )

    session_management_client.register_multiplexer_sessions(
        _create_multiplexer_session_infos(multiplexer_session_count)
    )

    session_management_stub.RegisterMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.RegisterMultiplexerSessions.call_args.args
    assert len(request.multiplexer_sessions) == multiplexer_session_count
    assert [s.session.name for s in request.multiplexer_sessions] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]


@pytest.mark.parametrize("multiplexer_session_count", [0, 1, 2])
def test___varying_multiplexer_session_count___unregister_multiplexer_sessions___sends_request(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.UnregisterMultiplexerSessions.return_value = (
        session_management_service_pb2.UnregisterMultiplexerSessionsResponse()
    )

    session_management_client.unregister_multiplexer_sessions(
        _create_multiplexer_session_infos(multiplexer_session_count)
    )

    session_management_stub.UnregisterMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.UnregisterMultiplexerSessions.call_args.args
    assert len(request.multiplexer_sessions) == multiplexer_session_count
    assert [s.session.name for s in request.multiplexer_sessions] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]


def test___optional_arg___get_multiplexer_sessions___sends_request_with_args(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetMultiplexerSessions.return_value = (
        session_management_service_pb2.GetMultiplexerSessionsResponse()
    )

    session_management_client.get_multiplexer_sessions(
        PinMapContext("MyPinMap", [0, 1]), "multiplexer_type_id"
    )

    session_management_stub.GetMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetMultiplexerSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.multiplexer_type_id == "multiplexer_type_id"


def test___no_optional_args___get_multiplexer_sessions___sends_request_with_default(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetMultiplexerSessions.return_value = (
        session_management_service_pb2.GetMultiplexerSessionsResponse()
    )

    session_management_client.get_multiplexer_sessions(PinMapContext("MyPinMap", [0, 1]))

    session_management_stub.GetMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetMultiplexerSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.multiplexer_type_id == ""


def test___explicit_none___get_multiplexer_sessions___sends_request_with_default(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetMultiplexerSessions.return_value = (
        session_management_service_pb2.GetMultiplexerSessionsResponse()
    )

    session_management_client.get_multiplexer_sessions(PinMapContext("MyPinMap", [0, 1]), None)

    session_management_stub.GetMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetMultiplexerSessions.call_args.args
    assert request.pin_map_context.pin_map_id == "MyPinMap"
    assert request.pin_map_context.sites == [0, 1]
    assert request.multiplexer_type_id == ""


@pytest.mark.parametrize("multiplexer_session_count", [0, 1, 2])
def test___varying_multiplexers___get_multiplexer_sessions___returns_multiplexer_session_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.GetMultiplexerSessions.return_value = (
        session_management_service_pb2.GetMultiplexerSessionsResponse(
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count)
        )
    )

    result = session_management_client.get_multiplexer_sessions(PinMapContext("MyPinMap", [0, 1]))

    session_management_stub.GetMultiplexerSessions.assert_called_once()
    assert len(result.multiplexer_session_info) == multiplexer_session_count
    assert [info.session_name for info in result.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]


def test___optional_arg___get_all_registered_multiplexer_sessions___sends_request_with_args(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetAllRegisteredMultiplexerSessions.return_value = (
        session_management_service_pb2.GetAllRegisteredMultiplexerSessionsResponse()
    )

    session_management_client.get_all_registered_multiplexer_sessions("multiplexer_type_id")

    session_management_stub.GetAllRegisteredMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetAllRegisteredMultiplexerSessions.call_args.args
    assert request.multiplexer_type_id == "multiplexer_type_id"


def test___no_optional_args___get_all_registered_multiplexer_sessions___sends_request_with_default(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetAllRegisteredMultiplexerSessions.return_value = (
        session_management_service_pb2.GetAllRegisteredMultiplexerSessionsResponse()
    )

    session_management_client.get_all_registered_multiplexer_sessions()

    session_management_stub.GetAllRegisteredMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetAllRegisteredMultiplexerSessions.call_args.args
    assert request.multiplexer_type_id == ""


def test___explicit_none___get_all_registered_multiplexer_sessions___sends_request_with_default(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
) -> None:
    session_management_stub.GetAllRegisteredMultiplexerSessions.return_value = (
        session_management_service_pb2.GetAllRegisteredMultiplexerSessionsResponse()
    )

    session_management_client.get_all_registered_multiplexer_sessions(None)

    session_management_stub.GetAllRegisteredMultiplexerSessions.assert_called_once()
    (request,) = session_management_stub.GetAllRegisteredMultiplexerSessions.call_args.args
    assert request.multiplexer_type_id == ""


@pytest.mark.parametrize("multiplexer_session_count", [0, 1, 2])
def test___varying_registered_multiplexers___get_all_registered_multiplexer_sessions___returns_multiplexer_session_infos(
    session_management_client: SessionManagementClient,
    session_management_stub: Mock,
    multiplexer_session_count: int,
) -> None:
    session_management_stub.GetAllRegisteredMultiplexerSessions.return_value = (
        session_management_service_pb2.GetAllRegisteredMultiplexerSessionsResponse(
            multiplexer_sessions=_create_grpc_multiplexer_session_infos(multiplexer_session_count)
        )
    )

    result = session_management_client.get_all_registered_multiplexer_sessions()

    session_management_stub.GetAllRegisteredMultiplexerSessions.assert_called_once()
    assert len(result.multiplexer_session_info) == multiplexer_session_count
    assert [info.session_name for info in result.multiplexer_session_info] == [
        f"MyMultiplexer{i}" for i in range(multiplexer_session_count)
    ]


def _create_session_infos(session_count: int) -> list[SessionInformation]:
    return [
        SessionInformation(f"MySession{i}", "", "", "", False, []) for i in range(session_count)
    ]


def _create_multiplexer_session_infos(
    multiplexer_session_count: int,
) -> list[MultiplexerSessionInformation]:
    return [
        MultiplexerSessionInformation(f"MyMultiplexer{i}", "", "", False)
        for i in range(multiplexer_session_count)
    ]


def _create_grpc_session_infos(
    session_count: int,
) -> list[session_management_service_pb2.SessionInformation]:
    return [
        session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=f"MySession{i}")
        )
        for i in range(session_count)
    ]


def _create_grpc_multiplexer_session_infos(
    session_count: int,
) -> list[session_management_service_pb2.MultiplexerSessionInformation]:
    return [
        session_management_service_pb2.MultiplexerSessionInformation(
            session=session_pb2.Session(name=f"MyMultiplexer{i}"),
            multiplexer_type_id=f"MyMultiplexerType{i}",
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
        "ni_measurement_plugin_sdk_service.session_management.SessionManagementClient._get_stub",
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
    stub.RegisterMultiplexerSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnregisterMultiplexerSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.GetMultiplexerSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.GetAllRegisteredMultiplexerSessions = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    return stub

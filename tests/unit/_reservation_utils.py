"""Reservation-related unit test utilities."""

from typing import List

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.session_management import SessionInformation
from tests.utilities import fake_driver


def create_grpc_session_infos(
    instrument_type_id: str,
    session_count: int,
) -> List[session_management_service_pb2.SessionInformation]:
    """Create a list of gRPC SessionInformation messages."""
    return [
        session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=f"MySession{i}"),
            resource_name=f"Dev{i}",
            instrument_type_id=instrument_type_id,
        )
        for i in range(session_count)
    ]


def create_grpc_multiplexer_session_infos(
    multiplexer_type_id: str,
    session_count: int,
) -> List[session_management_service_pb2.MultiplexerSessionInformation]:
    """Create a list of gRPC MultiplexerSessionInformation messages."""
    return [
        session_management_service_pb2.MultiplexerSessionInformation(
            session=session_pb2.Session(name=f"MyMultiplexer{i}"),
            resource_name=f"Mux{i}",
            multiplexer_type_id=multiplexer_type_id,
        )
        for i in range(session_count)
    ]


def construct_session(session_info: SessionInformation) -> fake_driver.Session:
    """Constructs a session object."""
    return fake_driver.Session(session_info.resource_name)

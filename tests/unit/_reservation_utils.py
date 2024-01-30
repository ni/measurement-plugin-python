"""Reservation-related unit test utilities."""

from typing import List

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)


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

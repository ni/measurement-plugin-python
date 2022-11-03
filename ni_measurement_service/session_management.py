"""Contains methods related to managing driver sessions."""
from functools import cached_property
from typing import Iterable, List, NamedTuple

import grpc

from ni_measurement_service._internal.stubs.ni.measurementlink import pin_map_context_pb2
from ni_measurement_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
    session_management_service_pb2_grpc,
)

GRPC_SERVICE_INTERFACE_NAME = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"
GRPC_SERVICE_CLASS = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"


class PinMapContext(NamedTuple):
    """Container for the pin map and sites."""

    pin_map_id: str
    sites: List[int]


class SessionInformation(NamedTuple):
    """Container for the session information."""

    session: str
    resource_name: str
    channel_list: str
    instrument_type_id: str
    session_exists: bool


class Reservation(object):
    """Manage session reservation."""

    def __init__(
        self,
        session_manager: "Client",
        session_info: Iterable[session_management_service_pb2.SessionInformation],
    ):
        """Initialise Reservation."""
        self._session_manager = session_manager
        self._session_info = session_info

    def __enter__(self):
        """Context management protocol. Returns self."""
        return self

    def __exit__(self, *exc):
        """Context management protocol. Calls unreserve()."""
        self.unreserve()
        return False

    def unreserve(self):
        """Unreserve sessions."""
        self._session_manager._unreserve_sessions(self._session_info)

    @cached_property
    def session_info(self) -> List[SessionInformation]:
        """Return session information."""
        return [
            SessionInformation(
                session=info.session.name,
                resource_name=info.resource_name,
                channel_list=info.channel_list,
                instrument_type_id=info.instrument_type_id,
                session_exists=info.session_exists,
            )
            for info in self._session_info
        ]


class Client(object):
    """Class that manages driver sessions."""

    def __init__(self, *, grpc_channel: grpc.Channel):
        """Initialise SessionManager."""
        self._client: session_management_service_pb2_grpc.SessionManagementServiceStub = (
            session_management_service_pb2_grpc.SessionManagementServiceStub(grpc_channel)
        )

    def reserve_sessions(
        self,
        pin_names: Iterable[str],
        instrument_type_id: str,
        context: PinMapContext,
        timeout: float = -1.0,
    ) -> Reservation:
        """Reserves sessions.

        Reserves session(s) for the given pins, sites, and instrument type and return the session
        names and channel lists.

        Returns the session name for each session, which allows the measurement service to get or
        create the session. Also returns the channel list.
        Also reserves the session (in Session Managers's own session reservation system) so other
        processes cannot access it.
        The request message for this method includes a timeout value, which allows the client to
        specify no timeout, infinite timeout, or a timeout value in milliseconds.
        Error occurs if the session cannot be reserved because a session by that name is already
        reserved, when timeout is set to 0 or a positive numeric value.
        """
        timeout_in_ms = int(timeout * 1000)
        if timeout_in_ms < 0:
            timeout_in_ms = -1

        pin_map_context = pin_map_context_pb2.PinMapContext(
            pin_map_id=context.pin_map_id, sites=context.sites
        )

        request = session_management_service_pb2.ReserveSessionsRequest(
            pin_names=pin_names,
            instrument_type_id=instrument_type_id,
            pin_map_context=pin_map_context,
            timeout_in_milliseconds=timeout_in_ms,
        )
        response: session_management_service_pb2.ReserveSessionsResponse = (
            self._client.ReserveSessions(request)
        )

        return Reservation(
            session_manager=self,
            session_info=response.sessions,
        )

    def _unreserve_sessions(
        self, session_info: Iterable[session_management_service_pb2.SessionInformation]
    ):
        """Unreserves sessions so they can be accessed by other clients."""
        request = session_management_service_pb2.UnreserveSessionsRequest(sessions=session_info)
        self._client.UnreserveSessions(request)

    def register_sessions(self, session_info: Iterable[SessionInformation]):
        """Register the sessions with the Session Manager.

        Indicates that the sessions are open and will need to be closed later.

        Error occurs if a session by the same name is already registered.
        """
        request = session_management_service_pb2.RegisterSessionsRequest(
            sessions=(
                session_management_service_pb2.SessionInformation(
                    session=session_management_service_pb2.Session(name=info.session),
                    resource_name=info.resource_name,
                    channel_list=info.channel_list,
                    instrument_type_id=info.instrument_type_id,
                    session_exists=info.session_exists,
                )
                for info in session_info
            )
        )
        self._client.RegisterSessions(request)

    def unregister_sessions(self, session_info: Iterable[SessionInformation]):
        """Unregisters the sessions from the Session Manager.

        Indicates that the sessions have been closed and will need to be reopened before they can be
        used again.
        """
        request = session_management_service_pb2.UnregisterSessionsRequest(
            sessions=(
                session_management_service_pb2.SessionInformation(
                    session=session_management_service_pb2.Session(name=info.session),
                    resource_name=info.resource_name,
                    channel_list=info.channel_list,
                    instrument_type_id=info.instrument_type_id,
                    session_exists=info.session_exists,
                )
                for info in session_info
            )
        )
        self._client.UnregisterSessions(request)

    def reserve_all_registered_sessions(self) -> Reservation:
        """Reserves and gets all sessions currently registered in the Session Manager."""
        request = session_management_service_pb2.ReserveAllRegisteredSessionsRequest()
        response: session_management_service_pb2.ReserveAllRegisteredSessionsResponse = (
            self._client.ReserveAllRegisteredSessions(request)
        )
        return Reservation(session_manager=self, session_info=response.sessions)

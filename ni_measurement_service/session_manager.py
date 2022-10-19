"""Contains methods related to managing driver sessions."""
from typing import Iterable
from typing import List
from typing import NamedTuple
from typing import Optional

import grpc

from ni_measurement_service import DiscoveryClient
from ni_measurement_service._internal.stubs import SessionManager_pb2
from ni_measurement_service._internal.stubs import SessionManager_pb2_grpc


class PinMapContext(NamedTuple):
    """Container for the pin map and sites."""

    pin_map_id: str
    sites: List[int]


class SessionInformation(NamedTuple):
    """Container for the pin map and sites."""

    session: str
    resource_name: str
    channel_list: str
    instrument_type_id: str
    session_exists: bool


class SessionManager(object):
    """Class that manages driver sessions."""

    _stub: SessionManager_pb2_grpc.RegistryServiceStub

    def __init__(
        self, *, session_manager_stub: Optional[SessionManager_pb2_grpc.SessionManagerStub] = None
    ):
        """Initialise SessionManager."""
        if session_manager_stub is None:
            discovery_client = DiscoveryClient()
            service_location = discovery_client.resolve_service("SessionManager")
            channel = grpc.insecure_channel(
                f"{service_location.location}:{service_location.insecure_port}"
            )
            session_manager_stub = SessionManager_pb2_grpc.RegistryServiceStub(channel)

        self._stub = session_manager_stub

    def reserve_sessions(
        self,
        pin_names: Iterable[str],
        instrument_type_id: str,
        context: PinMapContext,
        timeout: float = -1.0,
    ) -> Iterable[SessionInformation]:
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

        request = SessionManager_pb2.ReserveSessionsRequest(
            pin_names=pin_names,
            instrument_type_id=instrument_type_id,
            context=context,
            timeout_in_milliseconds=timeout_in_ms,
        )
        response = self._stub.ReserveSessions(request)

        for session in response.sessions:
            yield SessionInformation(*(session[f] for f in SessionInformation._fields))

    def unreserve_sessions(self, session_names: Iterable[str]):
        """Unreserves sessions so they can be accessed by other clients."""
        request = SessionManager_pb2.UnreserveSessionsRequest(session_names=session_names)
        self._stub.UnreserveSessions(request)

    def register_sessions(self, session_names: Iterable[str], context: PinMapContext):
        """Register the sessions with the Session Manager.

        Indicates that the sessions are open and will need to be closed later.

        Error occurs if a session by the same name is already registered.
        """
        request = SessionManager_pb2.RegisterSessionsRequest(
            session_names=session_names, context=context
        )
        self._stub.RegisterSessions(request)

    def unregister_sessions(self, session_names: Iterable[str]):
        """Unregisters the sessions from the Session Manager.

        Indicates that the sessions have been closed and will need to be reopened before they can be
        used again.
        """
        request = SessionManager_pb2.UnregisterSessionsRequest(session_names=session_names)
        self._stub.UnregisterSessions(request)

    def reserve_all_sessions_from_pin_map(
        self, context: PinMapContext
    ) -> Iterable[SessionInformation]:
        """Reserves and gets all session information from the pin map.

        Used in init code to create sessions.
        Returns the session name, resource name, channel list, and instrument type ID for each
        session.
        """
        request = SessionManager_pb2.ReserveAllSessionsFromPinMapRequest(context=context)
        response = self._stub.ReserveAllSessionsFromPinMap(request)
        for session in response.sessions:
            yield SessionInformation(*(session[f] for f in SessionInformation._fields))

    def reserve_all_registered_sessions(self) -> Iterable[SessionInformation]:
        """Reserves and gets all sessions currently registered in the Session Manager."""
        request = SessionManager_pb2.ReserveAllRegisteredSessionsRequest()
        response = self._stub.ReserveAllRegisteredSessions(request)
        for session in response.sessions:
            yield SessionInformation(*(session[f] for f in SessionInformation._fields))

"""Contains methods related to managing driver sessions."""
from functools import cached_property
from typing import Iterable, List, NamedTuple, Optional

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
        context: PinMapContext,
        pin_names: Optional[Iterable[str]] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Reservation:
        """Reserve session(s).

        Reserve session(s) for the given pins, sites, and instrument type ID and returns the
        information needed to create or access the session.

        Args
        ----
            context (PinMapContext): Includes the pin map ID for the pin map in the Pin Map Service,
                as well as the list of sites for the measurement.

            pin_names (Iterable[str]): List of pin names or pin group names to use for the
                measurement. If unspecified, reserve sessions for all pins in the registered pin map
                resource.

            instrument_type_id (str): Instrument type ID for the measurement. If unspecified,
                reserve sessions for all instrument types connected in the registered pin map
                resource. Pin maps have built in instrument definitions using the following NI
                driver based instrument type ids:
                    "niDCPower"
                    "niDigitalPattern"
                    "niScope"
                    "niDMM"
                    "niDAQmx".
                For custom instruments the user defined instrument type id is defined in the pin
                map file.

            timeout (float): Timeout in seconds. Allowed values,
                0 (non-blocking, fails immediately if resources cannot be reserved),
                -1 or negative (infinite timeout), or
                any  positive numeric value (wait for that number of second).

        Returns
        -------
            Reservation: Context manager that can be used with a with-statement to unreserve the
            sessions.

        """
        pin_map_context = pin_map_context_pb2.PinMapContext(
            pin_map_id=context.pin_map_id, sites=context.sites
        )

        request_kwargs: dict = {"pin_map_context": pin_map_context}
        if instrument_type_id is not None:
            request_kwargs["instrument_type_id"] = instrument_type_id
        if pin_names is not None:
            request_kwargs["pin_names"] = pin_names
        if timeout is not None:
            timeout_in_ms = round(timeout * 1000)
            if timeout_in_ms < 0:
                timeout_in_ms = -1
            request_kwargs["timeout_in_milliseconds"] = timeout_in_ms
        request = session_management_service_pb2.ReserveSessionsRequest(**request_kwargs)

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

        Args:
        ----
            session_info (Iterable[SessionInformation]): Sessions to register with the session
            management service to track as the sessions are open.

        Raises
        ------
            Exception: If a session by the same name is already registered.

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

        Args:
        ----
            session_info (Iterable[SessionInformation]): Sessions to be registered.

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
        """Reserves and gets all sessions currently registered in the Session Manager.

        Returns
        -------
            Reservation: Context manager that can be used with a with-statement to unreserve the
            sessions.

        """
        request = session_management_service_pb2.ReserveAllRegisteredSessionsRequest()
        response: session_management_service_pb2.ReserveAllRegisteredSessionsResponse = (
            self._client.ReserveAllRegisteredSessions(request)
        )
        return Reservation(session_manager=self, session_info=response.sessions)

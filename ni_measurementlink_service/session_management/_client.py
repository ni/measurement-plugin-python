"""Session management client class."""
from __future__ import annotations

import logging
import threading
import warnings
from typing import Iterable, Optional, Sequence, Union

import grpc

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
    session_management_service_pb2_grpc,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.session_management._constants import (
    GRPC_SERVICE_CLASS,
    GRPC_SERVICE_INTERFACE_NAME,
)
from ni_measurementlink_service.session_management._reservation import (
    MultiSessionReservation,
    SingleSessionReservation,
)
from ni_measurementlink_service.session_management._types import (
    PinMapContext,
    SessionInformation,
)

_logger = logging.getLogger(__name__)


class SessionManagementClient(object):
    """Client for accessing the MeasurementLink session management service."""

    def __init__(
        self,
        *,
        discovery_client: Optional[DiscoveryClient] = None,
        grpc_channel: Optional[grpc.Channel] = None,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ) -> None:
        """Initialize session management client.

        Args:
            discovery_client: An optional discovery client (recommended).

            grpc_channel: An optional session management gRPC channel.

            grpc_channel_pool: An optional gRPC channel pool (recommended).
        """
        self._initialization_lock = threading.Lock()
        self._discovery_client = discovery_client
        self._grpc_channel_pool = grpc_channel_pool
        self._stub: Optional[
            session_management_service_pb2_grpc.SessionManagementServiceStub
        ] = None

        if grpc_channel is not None:
            self._stub = session_management_service_pb2_grpc.SessionManagementServiceStub(
                grpc_channel
            )

    def _get_stub(self) -> session_management_service_pb2_grpc.SessionManagementServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    _logger.debug("Creating unshared GrpcChannelPool.")
                    self._grpc_channel_pool = GrpcChannelPool()
                if self._discovery_client is None:
                    _logger.debug("Creating unshared DiscoveryClient.")
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._grpc_channel_pool
                    )
                if self._stub is None:
                    service_location = self._discovery_client.resolve_service(
                        provided_interface=GRPC_SERVICE_INTERFACE_NAME,
                        service_class=GRPC_SERVICE_CLASS,
                    )
                    channel = self._grpc_channel_pool.get_channel(service_location.insecure_address)
                    self._stub = session_management_service_pb2_grpc.SessionManagementServiceStub(
                        channel
                    )
        return self._stub

    def reserve_session(
        self,
        context: PinMapContext,
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = 0.0,
    ) -> SingleSessionReservation:
        """Reserve a single session.

        Reserve the session matching the given pins, sites, and instrument type ID and return the
        information needed to create or access the session.

        Args:
            context: Includes the pin map ID for the pin map in the Pin Map Service,
                as well as the list of sites for the measurement.

            pin_or_relay_names: One or multiple pins, pin groups, relays, or relay groups to use
                for the measurement.

                If unspecified, reserve sessions for all pins and relays in the registered pin map
                resource.

            instrument_type_id: Instrument type ID for the measurement.

                If unspecified, this method reserve sessions for all instrument types connected
                in the registered pin map resource.

                For NI instruments, use instrument type id constants, such as
                :py:const:`INSTRUMENT_TYPE_NI_DCPOWER` or :py:const:`INSTRUMENT_TYPE_NI_DMM`.

                For custom instruments, use the instrument type id defined in the pin map file.

            timeout: Timeout in seconds.

                Allowed values: 0 (non-blocking, fails immediately if resources cannot be
                reserved), -1 (infinite timeout), or any other positive numeric value (wait for
                that number of seconds)

        Returns:
            A reservation object with which you can query information about the session and
            unreserve it.
        """
        session_info = self._reserve_sessions(
            context, pin_or_relay_names, instrument_type_id, timeout
        )
        if len(session_info) == 0:
            raise ValueError("No sessions reserved. Expected single session, got 0 sessions.")
        elif len(session_info) > 1:
            self._unreserve_sessions(session_info)
            raise ValueError(
                "Too many sessions reserved. Expected single session, got "
                f"{len(session_info)} sessions."
            )
        else:
            return SingleSessionReservation(
                session_manager=self,
                session_info=session_info,
                reserved_pin_or_relay_names=pin_or_relay_names,
                reserved_sites=context.sites,
            )

    def reserve_sessions(
        self,
        context: PinMapContext,
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = 0.0,
    ) -> MultiSessionReservation:
        """Reserve multiple sessions.

        Reserve sessions matching the given pins, sites, and instrument type ID and return the
        information needed to create or access the sessions.

        Args:
            context: Includes the pin map ID for the pin map in the Pin Map Service,
                as well as the list of sites for the measurement.

            pin_or_relay_names: One or multiple pins, pin groups, relays, or relay groups to use
                for the measurement.

                If unspecified, reserve sessions for all pins and relays in the registered pin map
                resource.

            instrument_type_id: Instrument type ID for the measurement.

                If unspecified, this method reserves sessions for all instrument types connected
                in the registered pin map resource.

                For NI instruments, use instrument type id constants, such as
                :py:const:`INSTRUMENT_TYPE_NI_DCPOWER` or :py:const:`INSTRUMENT_TYPE_NI_DMM`.

                For custom instruments, use the instrument type id defined in the pin map file.

            timeout: Timeout in seconds.

                Allowed values: 0 (non-blocking, fails immediately if resources cannot be
                reserved), -1 (infinite timeout), or any other positive numeric value (wait for
                that number of seconds)

        Returns:
            A reservation object with which you can query information about the sessions and
            unreserve them.
        """
        session_info = self._reserve_sessions(
            context, pin_or_relay_names, instrument_type_id, timeout
        )
        return MultiSessionReservation(
            session_manager=self,
            session_info=session_info,
            reserved_pin_or_relay_names=pin_or_relay_names,
            reserved_sites=context.sites,
        )

    def _reserve_sessions(
        self,
        context: PinMapContext,
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = 0.0,
    ) -> Sequence[session_management_service_pb2.SessionInformation]:
        request = session_management_service_pb2.ReserveSessionsRequest(
            pin_map_context=context._to_grpc(),
            timeout_in_milliseconds=_timeout_to_milliseconds(timeout),
        )
        if instrument_type_id is not None:
            request.instrument_type_id = instrument_type_id
        if isinstance(pin_or_relay_names, str):
            request.pin_or_relay_names.append(pin_or_relay_names)
        elif pin_or_relay_names is not None:
            request.pin_or_relay_names.extend(pin_or_relay_names)

        response = self._get_stub().ReserveSessions(request)
        return response.sessions

    def _unreserve_sessions(
        self, session_info: Iterable[session_management_service_pb2.SessionInformation]
    ) -> None:
        """Unreserves sessions so they can be accessed by other clients."""
        request = session_management_service_pb2.UnreserveSessionsRequest(sessions=session_info)
        self._get_stub().UnreserveSessions(request)

    def register_sessions(self, session_info: Iterable[SessionInformation]) -> None:
        """Register sessions with the session management service.

        Indicates that the sessions are open and will need to be closed later.

        Args:
            session_info: Sessions to register.
        """
        request = session_management_service_pb2.RegisterSessionsRequest(
            sessions=(info._to_grpc_v1() for info in session_info),
        )
        self._get_stub().RegisterSessions(request)

    def unregister_sessions(self, session_info: Iterable[SessionInformation]) -> None:
        """Unregisters sessions from the session management service.

        Indicates that the sessions have been closed and will need to be reopened before they can be
        used again.

        Args:
            session_info: Sessions to unregister.
        """
        request = session_management_service_pb2.UnregisterSessionsRequest(
            sessions=(info._to_grpc_v1() for info in session_info),
        )
        self._get_stub().UnregisterSessions(request)

    def reserve_all_registered_sessions(
        self, instrument_type_id: Optional[str] = None, timeout: Optional[float] = 0.0
    ) -> MultiSessionReservation:
        """Reserve all sessions currently registered with the session management service.

        Args:
            instrument_type_id: Instrument type ID for the measurement.

                If unspecified, reserve sessions for all instrument types connected in the
                registered pin map resource.

                For NI instruments, use instrument type id constants, such as
                :py:const:`INSTRUMENT_TYPE_NI_DCPOWER` or :py:const:`INSTRUMENT_TYPE_NI_DMM`.

                For custom instruments, use the instrument type id defined in the pin map file.

            timeout: Timeout in seconds.

                Allowed values: 0 (non-blocking, fails immediately if resources cannot be
                reserved), -1 (infinite timeout), or any other positive numeric value (wait for
                that number of seconds)

        Returns:
            A reservation object with which you can query information about the sessions and
            unreserve them.
        """
        request = session_management_service_pb2.ReserveAllRegisteredSessionsRequest(
            timeout_in_milliseconds=_timeout_to_milliseconds(timeout)
        )
        if instrument_type_id is not None:
            request.instrument_type_id = instrument_type_id

        response = self._get_stub().ReserveAllRegisteredSessions(request)
        return MultiSessionReservation(session_manager=self, session_info=response.sessions)


def _timeout_to_milliseconds(timeout: Optional[float]) -> int:
    if timeout is None:
        return 0
    elif timeout == -1:
        return -1
    elif timeout < 0:
        warnings.warn("Specify -1 for an infinite timeout.", RuntimeWarning)
        return -1
    else:
        return round(timeout * 1000)

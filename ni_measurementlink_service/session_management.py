"""Contains methods related to managing driver sessions."""
from __future__ import annotations

import abc
import sys
import warnings
from functools import cached_property
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    Type,
)

import grpc
from deprecation import DeprecatedWarning

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink import (
    pin_map_context_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
    session_management_service_pb2_grpc,
)

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

GRPC_SERVICE_INTERFACE_NAME = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"
GRPC_SERVICE_CLASS = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"


# Constants for instrument_type_id parameters
INSTRUMENT_TYPE_NONE = ""
INSTRUMENT_TYPE_NI_DCPOWER = "niDCPower"
INSTRUMENT_TYPE_NI_HSDIO = "niHSDIO"
INSTRUMENT_TYPE_NI_RFSA = "niRFSA"
INSTRUMENT_TYPE_NI_RFMX = "niRFmx"
INSTRUMENT_TYPE_NI_RFSG = "niRFSG"
INSTRUMENT_TYPE_NI_RFPM = "niRFPM"
INSTRUMENT_TYPE_NI_DMM = "niDMM"
INSTRUMENT_TYPE_NI_DIGITAL_PATTERN = "niDigitalPattern"
INSTRUMENT_TYPE_NI_SCOPE = "niScope"
INSTRUMENT_TYPE_NI_FGEN = "niFGen"
INSTRUMENT_TYPE_NI_DAQMX = "niDAQmx"
INSTRUMENT_TYPE_NI_RELAY_DRIVER = "niRelayDriver"
INSTRUMENT_TYPE_NI_MODEL_BASED_INSTRUMENT = "niModelBasedInstrument"
INSTRUMENT_TYPE_NI_SWITCH_EXECUTIVE_VIRTUAL_DEVICE = "niSwitchExecutiveVirtualDevice"


class PinMapContext(NamedTuple):
    """Container for the pin map and sites.

    Attributes
    ----------
        pin_map_id: The resource id of the pin map in the Pin Map service that should be used for
            the call.

        sites: List of site numbers being used for the call. If None or empty, use all sites in the
            pin map.

    """

    pin_map_id: str
    sites: Optional[List[int]]


class ChannelMapping(NamedTuple):
    """Mapping of each channel to the pin and site it is connected to.

    Attributes
    ----------
        pin_or_relay_name (str): The pin or relay that is mapped to a channel.

        site (int): The site on which the pin or relay is mapped to a channel.
            For system pins/relays the site number is -1 as they do not belong to a specific site.

        channel (str): The channel to which the pin or relay is mapped on this site.

    """

    pin_or_relay_name: str
    site: int
    channel: str


class SessionInformation(NamedTuple):
    """Container for the session information.

    Attributes
    ----------
        session_name (str): Session identifier used to identify the session in the session
            management service, as well as in driver services such as grpc-device.

        resource_name (str): Resource name used to open this session in the driver.

        channel_list (str): Channel list used for driver initialization and measurement methods.
            This field is empty for any SessionInformation returned from
            Client.reserve_all_registered_sessions.

        instrument_type_id (str): Instrument type ID to identify which type of instrument the
            session represents. Pin maps have built in instrument definitions using the instrument
            type id constants such as `INSTRUMENT_TYPE_NI_DCPOWER`. For custom instruments, the
            user defined instrument type id is defined in the pin map file.

        session_exists (bool): Indicates whether the session exists in the Session Manager. This
            indicates whether the session has been created.

        channel_mappings (Iterable[ChannelMapping]): List of site and pin/relay mappings that
            correspond to each channel in the channel_list. Each item contains a mapping
            for a channel in this instrument resource, in the order of the channel_list.
            This field is empty for any SessionInformation returned from
            Client.reserve_all_registered_sessions.

    """

    session_name: str
    resource_name: str
    channel_list: str
    instrument_type_id: str
    session_exists: bool
    channel_mappings: Iterable[ChannelMapping]


def _convert_channel_mapping_from_grpc(
    channel_mapping: session_management_service_pb2.ChannelMapping,
) -> ChannelMapping:
    return ChannelMapping(
        pin_or_relay_name=channel_mapping.pin_or_relay_name,
        site=channel_mapping.site,
        channel=channel_mapping.channel,
    )


def _convert_channel_mapping_to_grpc(
    channel_mapping: ChannelMapping,
) -> session_management_service_pb2.ChannelMapping:
    return session_management_service_pb2.ChannelMapping(
        pin_or_relay_name=channel_mapping.pin_or_relay_name,
        site=channel_mapping.site,
        channel=channel_mapping.channel,
    )


def _convert_session_info_from_grpc(
    session_info: session_management_service_pb2.SessionInformation,
) -> SessionInformation:
    return SessionInformation(
        session_name=session_info.session.name,
        resource_name=session_info.resource_name,
        channel_list=session_info.channel_list,
        instrument_type_id=session_info.instrument_type_id,
        session_exists=session_info.session_exists,
        channel_mappings=[
            _convert_channel_mapping_from_grpc(m) for m in session_info.channel_mappings
        ],
    )


def _convert_session_info_to_grpc(
    session_info: SessionInformation,
) -> session_management_service_pb2.SessionInformation:
    return session_management_service_pb2.SessionInformation(
        session=session_pb2.Session(name=session_info.session_name),
        resource_name=session_info.resource_name,
        channel_list=session_info.channel_list,
        instrument_type_id=session_info.instrument_type_id,
        session_exists=session_info.session_exists,
        channel_mappings=[
            _convert_channel_mapping_to_grpc(m) for m in session_info.channel_mappings
        ],
    )


class BaseReservation(abc.ABC):
    """Manages session reservation."""

    def __init__(
        self,
        session_manager: Client,
        session_info: Sequence[session_management_service_pb2.SessionInformation],
    ) -> None:
        """Initialize reservation object."""
        self._session_manager = session_manager
        self._session_info = session_info

    def __enter__(self: Self) -> Self:
        """Context management protocol. Returns self."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        """Context management protocol. Calls unreserve()."""
        self.unreserve()
        return False

    def unreserve(self) -> None:
        """Unreserve sessions."""
        self._session_manager._unreserve_sessions(self._session_info)


class SingleSessionReservation(BaseReservation):
    """Manages reservation for a single session."""

    @cached_property
    def session_info(self) -> SessionInformation:
        """Single session information object."""
        assert len(self._session_info) == 1
        return _convert_session_info_from_grpc(self._session_info[0])


class MultiSessionReservation(BaseReservation):
    """Manages reservation for multiple sessions."""

    @cached_property
    def session_info(self) -> List[SessionInformation]:
        """Multiple session information objects."""
        return [_convert_session_info_from_grpc(info) for info in self._session_info]


def __getattr__(name: str) -> Any:
    if name == "Reservation":
        warnings.warn(
            DeprecatedWarning(
                name,
                deprecated_in="1.1.0",
                removed_in=None,
                details="Use MultiSessionReservation instead.",
            ),
            stacklevel=2,
        )
        return MultiSessionReservation
    else:
        raise AttributeError(f"module {__name__} has no attribute {name}")


class SessionManagementClient(object):
    """Class that manages driver sessions."""

    def __init__(self, *, grpc_channel: grpc.Channel) -> None:
        """Initialize session manangement client."""
        self._client: session_management_service_pb2_grpc.SessionManagementServiceStub = (
            session_management_service_pb2_grpc.SessionManagementServiceStub(grpc_channel)
        )

    def reserve_session(
        self,
        context: PinMapContext,
        pin_or_relay_names: Optional[Iterable[str]] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> SingleSessionReservation:
        """Reserve a single session.

        Reserve the session matching the given pins, sites, and instrument type ID and return the
        information needed to create or access the session.

        Args
        ----
            context (PinMapContext): Includes the pin map ID for the pin map in the Pin Map Service,
                as well as the list of sites for the measurement.

            pin_or_relay_names (Iterable[str]): List of pins, pin groups, relays, or relay groups to
                use for the measurement. If unspecified, reserve sessions for all pins and relays in
                the registered pin map resource.

            instrument_type_id (str): Instrument type ID for the measurement. If unspecified,
                reserve sessions for all instrument types connected in the registered pin map
                resource. Pin maps have built in instrument definitions using the following NI
                driver based instrument type ids:
                    "niDCPower"
                    "niDigitalPattern"
                    "niScope"
                    "niDMM"
                    "niDAQmx"
                    "niFGen"
                    "niRelayDriver"
                For custom instruments the user defined instrument type id is defined in the pin
                map file.

            timeout (float): Timeout in seconds. Allowed values,
                0 (non-blocking, fails immediately if resources cannot be reserved),
                -1 or negative (infinite timeout), or
                any positive numeric value (wait for that number of second).

        Returns
        -------
            SingleSessionReservation: Context manager that can be used with a with-statement to
            unreserve the session.

        """
        session_info = self._reserve_sessions(
            context, pin_or_relay_names, instrument_type_id, timeout
        )
        if len(session_info) == 0:
            raise ValueError("No sessions reserved. Expected single session, got 0 sessions.")
        elif len(session_info) > 1:
            raise ValueError(
                "Too many sessions reserved. Expected single session, got "
                f"{len(session_info)} sessions."
            )
        else:
            return SingleSessionReservation(session_manager=self, session_info=session_info)

    def reserve_sessions(
        self,
        context: PinMapContext,
        pin_or_relay_names: Optional[Iterable[str]] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> MultiSessionReservation:
        """Reserve multiple sessions.

        Reserve sessions matching the given pins, sites, and instrument type ID and return the
        information needed to create or access the sessions.

        Args
        ----
            context (PinMapContext): Includes the pin map ID for the pin map in the Pin Map Service,
                as well as the list of sites for the measurement.

            pin_or_relay_names (Iterable[str]): List of pins, pin groups, relays, or relay groups to
                use for the measurement. If unspecified, reserve sessions for all pins and relays in
                the registered pin map resource.

            instrument_type_id (str): Instrument type ID for the measurement. If unspecified,
                reserve sessions for all instrument types connected in the registered pin map
                resource. Pin maps have built in instrument definitions using the following NI
                driver based instrument type ids:
                    "niDCPower"
                    "niDigitalPattern"
                    "niScope"
                    "niDMM"
                    "niDAQmx"
                    "niFGen"
                    "niRelayDriver"
                For custom instruments the user defined instrument type id is defined in the pin
                map file.

            timeout (float): Timeout in seconds. Allowed values,
                0 (non-blocking, fails immediately if resources cannot be reserved),
                -1 or negative (infinite timeout), or
                any positive numeric value (wait for that number of second).

        Returns
        -------
            MultiSessionReservation: Context manager that can be used with a with-statement to
            unreserve the sessions.

        """
        session_info = self._reserve_sessions(
            context, pin_or_relay_names, instrument_type_id, timeout
        )
        return MultiSessionReservation(session_manager=self, session_info=session_info)

    def _reserve_sessions(
        self,
        context: PinMapContext,
        pin_or_relay_names: Optional[Iterable[str]] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Sequence[session_management_service_pb2.SessionInformation]:
        pin_map_context = pin_map_context_pb2.PinMapContext(
            pin_map_id=context.pin_map_id, sites=context.sites
        )

        request = session_management_service_pb2.ReserveSessionsRequest(
            pin_map_context=pin_map_context
        )
        if instrument_type_id is not None:
            request.instrument_type_id = instrument_type_id
        if pin_or_relay_names is not None:
            request.pin_or_relay_names.extend(pin_or_relay_names)
        if timeout is not None:
            timeout_in_ms = round(timeout * 1000)
            if timeout_in_ms < 0:
                timeout_in_ms = -1
            request.timeout_in_milliseconds = timeout_in_ms

        response: session_management_service_pb2.ReserveSessionsResponse = (
            self._client.ReserveSessions(request)
        )

        return response.sessions

    def _unreserve_sessions(
        self, session_info: Iterable[session_management_service_pb2.SessionInformation]
    ) -> None:
        """Unreserves sessions so they can be accessed by other clients."""
        request = session_management_service_pb2.UnreserveSessionsRequest(sessions=session_info)
        self._client.UnreserveSessions(request)

    def register_sessions(self, session_info: Iterable[SessionInformation]) -> None:
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
                    session=session_pb2.Session(name=info.session_name),
                    resource_name=info.resource_name,
                    channel_list=info.channel_list,
                    instrument_type_id=info.instrument_type_id,
                    session_exists=info.session_exists,
                    channel_mappings=[
                        session_management_service_pb2.ChannelMapping(
                            pin_or_relay_name=channel_mapping.pin_or_relay_name,
                            site=channel_mapping.site,
                            channel=channel_mapping.channel,
                        )
                        for channel_mapping in info.channel_mappings
                    ],
                )
                for info in session_info
            )
        )
        self._client.RegisterSessions(request)

    def unregister_sessions(self, session_info: Iterable[SessionInformation]) -> None:
        """Unregisters the sessions from the Session Manager.

        Indicates that the sessions have been closed and will need to be reopened before they can be
        used again.

        Args:
            session_info (Iterable[SessionInformation]): Sessions to be registered.

        """
        request = session_management_service_pb2.UnregisterSessionsRequest(
            sessions=(
                session_management_service_pb2.SessionInformation(
                    session=session_pb2.Session(name=info.session_name),
                    resource_name=info.resource_name,
                    channel_list=info.channel_list,
                    instrument_type_id=info.instrument_type_id,
                    session_exists=info.session_exists,
                    channel_mappings=[
                        session_management_service_pb2.ChannelMapping(
                            pin_or_relay_name=channel_mapping.pin_or_relay_name,
                            site=channel_mapping.site,
                            channel=channel_mapping.channel,
                        )
                        for channel_mapping in info.channel_mappings
                    ],
                )
                for info in session_info
            )
        )
        self._client.UnregisterSessions(request)

    def reserve_all_registered_sessions(
        self, instrument_type_id: Optional[str] = None, timeout: Optional[float] = None
    ) -> MultiSessionReservation:
        """Reserves and gets all sessions currently registered in the Session Manager.

        Args
        ----
            instrument_type_id (str): Instrument type ID for the measurement. If unspecified,
                reserve sessions for all instrument types connected in the registered pin map
                resource. Pin maps have built in instrument definitions using the following NI
                driver based instrument type ids:
                    "niDCPower"
                    "niDigitalPattern"
                    "niScope"
                    "niDMM"
                    "niDAQmx"
                    "niFGen"
                    "niRelayDriver"
                For custom instruments the user defined instrument type id is defined in the pin
                map file.

            timeout (float): Timeout in seconds. Allowed values,
                0 (non-blocking, fails immediately if resources cannot be reserved),
                -1 or negative (infinite timeout), or
                any positive numeric value (wait for that number of second).

        Returns
        -------
            MultiSessionReservation: Context manager that can be used with a with-statement to
            unreserve the sessions.

        """
        request = session_management_service_pb2.ReserveAllRegisteredSessionsRequest()
        if instrument_type_id is not None:
            request.instrument_type_id = instrument_type_id
        if timeout is not None:
            timeout_in_ms = round(timeout * 1000)
            if timeout_in_ms < 0:
                timeout_in_ms = -1
            request.timeout_in_milliseconds = timeout_in_ms

        response: session_management_service_pb2.ReserveAllRegisteredSessionsResponse = (
            self._client.ReserveAllRegisteredSessions(request)
        )
        return MultiSessionReservation(session_manager=self, session_info=response.sessions)


Client = SessionManagementClient
"""Alias for compatibility with code that uses session_management.Client."""

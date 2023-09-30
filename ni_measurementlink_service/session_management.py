"""Client for accessing the MeasurementLink session management service."""
from __future__ import annotations

import abc
import contextlib
import logging
import sys
import threading
import warnings
from contextlib import ExitStack
from functools import cached_property
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Generic,
    Iterable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

import grpc
from deprecation import DeprecatedWarning

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._drivers import closing_session
from ni_measurementlink_service._featuretoggles import (
    SESSION_MANAGEMENT_2024Q1,
    requires_feature,
)
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
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

_logger = logging.getLogger(__name__)

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


TSession = TypeVar("TSession")
TSession_co = TypeVar("TSession_co", covariant=True)


class PinMapContext(NamedTuple):
    """Container for the pin map and sites."""

    pin_map_id: str
    """The resource id of the pin map in the Pin Map service that should be used for the call."""

    sites: Optional[List[int]]
    """List of site numbers being used for the call.
    
    If None or empty, use all sites in the pin map.
    """


class ChannelMapping(NamedTuple):
    """Mapping of each channel to the pin and site it is connected to."""

    pin_or_relay_name: str
    """The pin or relay that is mapped to a channel."""

    site: int
    """The site on which the pin or relay is mapped to a channel.
            
    For system pins/relays the site number is -1 as they do not belong to a specific site.
    """

    channel: str
    """The channel to which the pin or relay is mapped on this site."""


class SessionInformation(NamedTuple):
    """Container for the session information."""

    session_name: str
    """Session identifier used to identify the session in the session management service, as well
    as in driver services such as grpc-device.
    """

    resource_name: str
    """Resource name used to open this session in the driver."""

    channel_list: str
    """Channel list used for driver initialization and measurement methods.

    This field is empty for any SessionInformation returned from
    Client.reserve_all_registered_sessions.
    """

    instrument_type_id: str
    """Instrument type ID to identify which type of instrument the session represents.
    
    Pin maps have built in instrument definitions using the instrument
    type id constants such as `INSTRUMENT_TYPE_NI_DCPOWER`. For custom instruments, the
    user defined instrument type id is defined in the pin map file.
    """

    session_exists: bool
    """Indicates whether the session has been registered with the session management service.
    
    When calling measurements from TestStand, the test sequence's ``ProcessSetup`` callback
    creates instrument sessions and registers them with the session management service so that
    they can be shared between multiple measurement steps. In this case, the `session_exists`
    attribute is ``True``, indicating that the instrument sessions were already created and any
    one-time setup (such as creating NI-DAQmx channels or loading NI-Digital files) has been
    performed.
    
    When calling measurements outside of TestStand, the `session_exists` attribute is ``False``,
    indicating that the measurement is responsible for creating the instrument sessions and
    performing any one-time setup.
    """

    channel_mappings: Iterable[ChannelMapping]
    """List of site and pin/relay mappings that correspond to each channel in the channel_list.
     
    Each item contains a mapping for a channel in this instrument resource, in the order of the
    channel_list. This field is empty for any SessionInformation returned from
    Client.reserve_all_registered_sessions.
    """

    session: object = None
    """The driver session object.
    
    This field is None until the appropriate create_session(s) method is called.
    """

    def _with_session(self, session: TSession) -> TypedSessionInformation[TSession]:
        return cast(TypedSessionInformation[TSession], self._replace(session=session))


# Python versions <3.11 do not support generic named tuples, so we use a generic
# protocol to return typed session information.
class TypedSessionInformation(Protocol, Generic[TSession_co]):
    """Generic version of :any:`SessionInformation` that preserves the session type."""

    @property
    def session_name(self) -> str:
        """See :any:`SessionInformation.session_name`."""
        ...

    @property
    def resource_name(self) -> str:
        """See :any:`SessionInformation.resource_name`."""
        ...

    @property
    def channel_list(self) -> str:
        """See :any:`SessionInformation.channel_list`."""
        ...

    @property
    def instrument_type_id(self) -> str:
        """See :any:`SessionInformation.instrument_type_id`."""
        ...

    @property
    def session_exists(self) -> bool:
        """See :any:`SessionInformation.session_exists`."""
        ...

    @property
    def channel_mappings(self) -> Iterable[ChannelMapping]:
        """See :any:`SessionInformation.channel_mappings`."""
        ...

    @property
    def session(self) -> TSession_co:
        """See :any:`SessionInformation.session`."""
        ...


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
        self._session_cache: Dict[str, object] = {}

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

    @contextlib.contextmanager
    def _cache_session(self, session_name: str, session: TSession) -> Generator[None, None, None]:
        if session_name in self._session_cache:
            raise RuntimeError(f"Session '{session_name}' already exists.")
        self._session_cache[session_name] = session
        try:
            yield
        finally:
            del self._session_cache[session_name]

    @contextlib.contextmanager
    def _create_session_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> Generator[TypedSessionInformation[TSession], None, None]:
        session_infos = [
            _convert_session_info_from_grpc(info)
            for info in self._session_info
            if info.instrument_type_id == instrument_type_id
        ]
        if len(session_infos) == 0:
            raise ValueError(
                f"No sessions matched instrument type ID '{instrument_type_id}'. "
                "Expected single session, got 0 sessions."
            )
        elif len(session_infos) > 1:
            raise ValueError(
                f"Too many sessions matched instrument type ID '{instrument_type_id}'. "
                f"Expected single session, got {len(session_infos)} sessions."
            )

        session_info = session_infos[0]
        with closing_session(session_constructor(session_info)) as session:
            with self._cache_session(session_info.session_name, session):
                yield session_info._with_session(session)

    @contextlib.contextmanager
    def _create_sessions_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> Generator[Sequence[TypedSessionInformation[TSession]], None, None]:
        session_infos = [
            _convert_session_info_from_grpc(info)
            for info in self._session_info
            if info.instrument_type_id == instrument_type_id
        ]
        if len(session_infos) == 0:
            raise ValueError(
                f"No sessions matched instrument type ID '{instrument_type_id}'. "
                "Expected single or multiple sessions, got 0 sessions."
            )

        with ExitStack() as stack:
            typed_session_infos: List[TypedSessionInformation[TSession]] = []
            for session_info in session_infos:
                session = stack.enter_context(closing_session(session_constructor(session_info)))
                stack.enter_context(self._cache_session(session_info.session_name, session))
                typed_session_infos.append(session_info._with_session(session))
            yield typed_session_infos

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_session(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> ContextManager[TypedSessionInformation[TSession]]:
        """Create a single instrument session.

        This is a generic method that supports any instrument driver.

        Args:
            session_constructor: A function that constructs sessions based on session
                information.
            instrument_type_id: Instrument type ID for the session.
                For NI instruments, use instrument type id constants, such as
                :py:const:`INSTRUMENT_TYPE_NI_DCPOWER` or :py:const:`INSTRUMENT_TYPE_NI_DMM`.
                For custom instruments, use the instrument type id defined in the pin map file.

        Returns:
            A context manager that yields a tuple of session information and session objects.
        """
        return self._create_session_core(session_constructor, instrument_type_id)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_sessions(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> ContextManager[Sequence[TypedSessionInformation[TSession]]]:
        """Create multiple instrument sessions.

        This is a generic method that supports any instrument driver.

        Args:
            session_constructor: A function that constructs sessions based on session
                information.
            instrument_type_id: Instrument type ID for the session.
                For NI instruments, use instrument type id constants, such as
                :py:const:`INSTRUMENT_TYPE_NI_DCPOWER` or :py:const:`INSTRUMENT_TYPE_NI_DMM`.
                For custom instruments, use the instrument type id defined in the pin map file.

        Returns:
            A context manager that yields a sequence of tuples of session information and
            session objects.
        """
        return self._create_sessions_core(session_constructor, instrument_type_id)


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
            return SingleSessionReservation(session_manager=self, session_info=session_info)

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
        return MultiSessionReservation(session_manager=self, session_info=session_info)

    def _reserve_sessions(
        self,
        context: PinMapContext,
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        instrument_type_id: Optional[str] = None,
        timeout: Optional[float] = 0.0,
    ) -> Sequence[session_management_service_pb2.SessionInformation]:
        pin_map_context = pin_map_context_pb2.PinMapContext(
            pin_map_id=context.pin_map_id, sites=context.sites
        )

        request = session_management_service_pb2.ReserveSessionsRequest(
            pin_map_context=pin_map_context,
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
        self._get_stub().RegisterSessions(request)

    def unregister_sessions(self, session_info: Iterable[SessionInformation]) -> None:
        """Unregisters sessions from the session management service.

        Indicates that the sessions have been closed and will need to be reopened before they can be
        used again.

        Args:
            session_info: Sessions to unregister.
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


Client = SessionManagementClient
"""Alias for compatibility with code that uses session_management.Client."""


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

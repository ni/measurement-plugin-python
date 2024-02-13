"""Session management data types."""

from __future__ import annotations

from enum import IntEnum
from typing import Generic, Iterable, List, NamedTuple, Optional, Protocol, TypeVar

from ni_measurementlink_service._internal.stubs import session_pb2
from ni_measurementlink_service._internal.stubs.ni.measurementlink import (
    pin_map_context_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)

TSession = TypeVar("TSession")
TSession_co = TypeVar("TSession_co", covariant=True)
TMultiplexerSession = TypeVar("TMultiplexerSession")
TMultiplexerSession_co = TypeVar("TMultiplexerSession_co", covariant=True)


class PinMapContext(NamedTuple):
    """Container for the pin map and sites."""

    pin_map_id: str
    """The resource id of the pin map in the Pin Map service that should be used for the call."""

    sites: Optional[List[int]]
    """List of site numbers being used for the call.
    
    If None or empty, use all sites in the pin map.
    """

    @classmethod
    def _from_grpc(
        cls,
        other: pin_map_context_pb2.PinMapContext,
    ) -> PinMapContext:
        # The protobuf PinMapContext sites field is a RepeatedScalarContainer, not a list.
        # Constructing a protobuf PinMapContext with sites=None sets sites to an empty
        # RepeatedScalarContainer, not None.
        return PinMapContext(pin_map_id=other.pin_map_id, sites=list(other.sites))

    def _to_grpc(self) -> pin_map_context_pb2.PinMapContext:
        return pin_map_context_pb2.PinMapContext(pin_map_id=self.pin_map_id, sites=self.sites)


class ChannelMapping(NamedTuple):
    """Mapping of each channel to the pin and site it is connected to."""

    pin_or_relay_name: str
    """The pin or relay that is mapped to a channel."""

    site: int
    """The site on which the pin or relay is mapped to a channel.
            
    For system pins/relays, the site number is :any:`SITE_SYSTEM_PINS` (-1) as they
    do not belong to a specific site.
    """

    channel: str
    """The channel to which the pin or relay is mapped on this site."""

    multiplexer_resource_name: str
    """The multiplexer resource name used to open this session in the driver."""

    multiplexer_route: str
    """The multiplexer route through which the pin is connected to an instrument's channel."""

    @classmethod
    def _from_grpc_v1(cls, other: session_management_service_pb2.ChannelMapping) -> ChannelMapping:
        return ChannelMapping(
            pin_or_relay_name=other.pin_or_relay_name,
            site=other.site,
            channel=other.channel,
            multiplexer_resource_name=other.multiplexer_resource_name,
            multiplexer_route=other.multiplexer_route,
        )

    def _to_grpc_v1(self) -> session_management_service_pb2.ChannelMapping:
        return session_management_service_pb2.ChannelMapping(
            pin_or_relay_name=self.pin_or_relay_name,
            site=self.site,
            channel=self.channel,
            multiplexer_resource_name=self.multiplexer_resource_name,
            multiplexer_route=self.multiplexer_route,
        )


class SessionInformation(NamedTuple):
    """Container for the session information."""

    session_name: str
    """Session name used by the session management service and NI gRPC Device Server."""

    resource_name: str
    """Resource name used to open this session in the driver."""

    channel_list: str
    """Channel list used for driver initialization and measurement methods.

    This field is empty for any SessionInformation returned from
    Client.reserve_all_registered_sessions.
    """

    instrument_type_id: str
    """Indicates the instrument type for this session.
    
    Pin maps have built in instrument definitions using the instrument
    type id constants such as `INSTRUMENT_TYPE_NI_DCPOWER`. For custom instruments, the
    user defined instrument type id is defined in the pin map file.
    """

    session_exists: bool
    """Indicates whether the session is registered with the session management service.
    
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
    """List of mappings from channels to pins and sites.
     
    Each item contains a mapping for a channel in this instrument resource, in the order of the
    channel_list. This field is empty for any SessionInformation returned from
    Client.reserve_all_registered_sessions.
    """

    session: object = None
    """The driver session object.
    
    This field is None until the appropriate initialize_session(s) method is called.
    """

    def _check_runtime_type(self, session_type: type) -> None:
        if not isinstance(self.session, session_type):
            raise TypeError(
                f"Incorrect type for session '{self.session_name}'. "
                f"Expected {session_type}, got {type(self.session)}."
            )

    def _with_session(self, session: object) -> SessionInformation:
        if self.session is session:
            return self
        return self._replace(session=session)

    @classmethod
    def _from_grpc_v1(
        cls, other: session_management_service_pb2.SessionInformation
    ) -> SessionInformation:
        return SessionInformation(
            session_name=other.session.name,
            resource_name=other.resource_name,
            channel_list=other.channel_list,
            instrument_type_id=other.instrument_type_id,
            session_exists=other.session_exists,
            channel_mappings=[ChannelMapping._from_grpc_v1(m) for m in other.channel_mappings],
        )

    def _to_grpc_v1(
        self,
    ) -> session_management_service_pb2.SessionInformation:
        return session_management_service_pb2.SessionInformation(
            session=session_pb2.Session(name=self.session_name),
            resource_name=self.resource_name,
            channel_list=self.channel_list,
            instrument_type_id=self.instrument_type_id,
            session_exists=self.session_exists,
            channel_mappings=[m._to_grpc_v1() for m in self.channel_mappings],
        )


# Python versions <3.11 do not support generic named tuples, so we use a generic
# protocol to return typed session information.
class TypedSessionInformation(Protocol, Generic[TSession_co]):
    """Generic version of :any:`SessionInformation` that preserves the session type.

    For more details, see the corresponding documentation for :any:`SessionInformation`.
    """

    @property
    def session_name(self) -> str:
        """Session name used by the session management service and NI gRPC Device Server."""
        ...

    @property
    def resource_name(self) -> str:
        """Resource name used to open this session in the driver."""
        ...

    @property
    def channel_list(self) -> str:
        """Channel list used for driver initialization and measurement methods."""
        ...

    @property
    def instrument_type_id(self) -> str:
        """Indicates the instrument type for this session."""
        ...

    @property
    def session_exists(self) -> bool:
        """Indicates whether the session is registered with the session management service."""
        ...

    @property
    def channel_mappings(self) -> Iterable[ChannelMapping]:
        """List of mappings from channels to pins and sites."""
        ...

    @property
    def session(self) -> TSession_co:
        """The driver session object."""
        ...


class MultiplexerSessionInformation(NamedTuple):
    """Container for the multiplexer session information."""

    session_name: str
    """Session name used by the session management service and NI gRPC Device Server."""

    resource_name: str
    """Resource name used to open this session in the driver."""

    multiplexer_type_id: str
    """User-defined identifier for the multiplexer type in the pin map editor."""

    session_exists: bool
    """Indicates whether the session is registered with the session management service.
    
    When calling measurements from TestStand, the test sequence's ``ProcessSetup`` callback
    creates instrument sessions and registers them with the session management service so that
    they can be shared between multiple measurement steps. In this case, the `session_exists`
    attribute is ``True``, indicating that the instrument sessions were already created and any
    one-time setup has been performed.
    
    When calling measurements outside of TestStand, the `session_exists` attribute is ``False``,
    indicating that the measurement is responsible for creating the instrument sessions and
    performing any one-time setup.
    """

    session: object = None
    """The driver session object.
    
    This field is None until the appropriate initialize_multiplexer_session(s) method is called.
    """

    def _check_runtime_type(self, multiplexer_session_type: type) -> None:
        if not isinstance(self.session, multiplexer_session_type):
            raise TypeError(
                f"Incorrect type for multiplexer session '{self.session_name}'. "
                f"Expected {multiplexer_session_type}, got {type(self.session)}."
            )

    def _with_session(self, session: object) -> MultiplexerSessionInformation:
        if self.session is session:
            return self
        return self._replace(session=session)

    @classmethod
    def _from_grpc_v1(
        cls, other: session_management_service_pb2.MultiplexerSessionInformation
    ) -> MultiplexerSessionInformation:
        return MultiplexerSessionInformation(
            session_name=other.session.name,
            resource_name=other.resource_name,
            multiplexer_type_id=other.multiplexer_type_id,
            session_exists=other.session_exists,
        )

    def _to_grpc_v1(self) -> session_management_service_pb2.MultiplexerSessionInformation:
        return session_management_service_pb2.MultiplexerSessionInformation(
            session=session_pb2.Session(name=self.session_name),
            resource_name=self.resource_name,
            multiplexer_type_id=self.multiplexer_type_id,
            session_exists=self.session_exists,
        )


class TypedMultiplexerSessionInformation(Protocol, Generic[TMultiplexerSession_co]):
    """Generic version of :any:`MultiplexerSessionInformation` that preserves the session type.

    For more details, see the corresponding documentation of :any:`MultiplexerSessionInformation`.
    """

    @property
    def session_name(self) -> str:
        """Session name used by the session management service and NI gRPC Device Server."""
        ...

    @property
    def resource_name(self) -> str:
        """Resource name used to open this session in the driver."""
        ...

    @property
    def multiplexer_type_id(self) -> str:
        """User-defined identifier for the multiplexer type in the pin map editor."""
        ...

    @property
    def session_exists(self) -> bool:
        """Indicates whether the session is registered with the session management service."""
        ...

    @property
    def session(self) -> TMultiplexerSession_co:
        """The driver session object."""
        ...


class Connection(NamedTuple):
    """Describes the connection between an instance of a pin and an instrument channel.

    This object maps a pin or relay on a specific site to the corresponding
    instrument session and channel name.
    """

    pin_or_relay_name: str
    """The pin or relay name."""

    site: int
    """The site number.
    
    For system pins/relays, the site number is :any:`SITE_SYSTEM_PINS` (-1) as they
    do not belong to a specific site.
    """

    channel_name: str
    """The instrument channel name."""

    session_info: SessionInformation
    """The instrument session information."""

    multiplexer_resource_name: str
    """Resource name used to open this session in the driver."""

    multiplexer_route: str
    """The multiplexer route through which the pin is connected to an instrument's channel."""

    multiplexer_session_info: Optional[MultiplexerSessionInformation]
    """The multiplexer session information."""

    @property
    def session(self) -> object:
        """The instrument session."""
        return self.session_info.session

    @property
    def multiplexer_session(self) -> object:
        """The multiplexer session."""
        if self.multiplexer_session_info:
            return self.multiplexer_session_info.session
        return None

    def _check_runtime_type(self, session_type: type) -> None:
        self.session_info._check_runtime_type(session_type)

    def _check_runtime_multiplexer_type(self, multiplexer_session_type: type) -> None:
        if self.multiplexer_session_info is not None:
            self.multiplexer_session_info._check_runtime_type(multiplexer_session_type)

    def _with_session(self, session: object) -> Connection:
        if self.session is session:
            return self
        return self._replace(session_info=self.session_info._with_session(session))

    def _with_multiplexer_session(self, session: object) -> Connection:
        if self.multiplexer_session_info is None or self.multiplexer_session is session:
            return self
        return self._replace(
            multiplexer_session_info=self.multiplexer_session_info._with_session(session)
        )


class TypedConnection(Protocol, Generic[TSession_co]):
    """Generic version of :any:`Connection` that preserves the session type.

    For more details, see the corresponding documentation for :any:`Connection`.
    """

    @property
    def pin_or_relay_name(self) -> str:
        """The pin or relay name."""
        ...

    @property
    def site(self) -> int:
        """The site number.

        For system pins/relays, the site number is :any:`SITE_SYSTEM_PINS` (-1) as they
        do not belong to a specific site.
        """
        ...

    @property
    def channel_name(self) -> str:
        """The instrument channel name."""
        ...

    @property
    def session_info(self) -> TypedSessionInformation[TSession_co]:
        """The instrument session information."""
        ...

    @property
    def session(self) -> TSession_co:
        """The instrument session."""
        ...


class TypedConnectionWithMultiplexer(
    TypedConnection[TSession_co], Protocol, Generic[TSession_co, TMultiplexerSession_co]
):
    """Generic version of `Connection` that preserves the instrument and multiplexer session type.

    For more details, see the corresponding documentation for `Connection`.
    """

    @property
    def multiplexer_resource_name(self) -> str:
        """Resource name used to open this session in the driver."""
        ...

    @property
    def multiplexer_type_id(self) -> str:
        """User-defined identifier for the multiplexer type in the pin map editor."""
        ...

    @property
    def multiplexer_route(self) -> str:
        """The multiplexer route through which the pin is connected to an instrument's channel."""
        ...

    @property
    def multiplexer_session_info(
        self,
    ) -> TypedMultiplexerSessionInformation[TMultiplexerSession_co]:
        """The multiplexer session information."""
        ...

    @property
    def multiplexer_session(self) -> TMultiplexerSession_co:
        """The multiplexer session."""
        ...


class SessionInitializationBehavior(IntEnum):
    """Specifies whether to initialize a new session or attach to an existing session."""

    AUTO = 0
    """
    The NI gRPC Device Server will attach to an existing session with the
    specified name if it exists, otherwise the server will initialize a new
    session.

    Note: When using the Session as a context manager and the context exits, the
    behavior depends on what happened when the constructor was called. If it
    resulted in a new session being initialized on the NI gRPC Device Server,
    then it will automatically close the server session. If it instead attached
    to an existing session, then it will detach from the server session and
    leave it open.
    """

    INITIALIZE_SERVER_SESSION = 1
    """
    Initialize a new session with the specified name.

    Note: When using the Session as a context manager and the context exits, it
    will automatically close the server session.
    """

    ATTACH_TO_SERVER_SESSION = 2
    """
    Attach to an existing session with the specified name.

    Note: When using the Session as a context manager and the context exits, it
    will detach from the server session and leave it open.
    """

    INITIALIZE_SESSION_THEN_DETACH = 3
    """
    Initialize a new session. 
    
    When exiting the context manager, detach instead of closing.

    Note: This initialization behavior is intended for TestStand code modules used in
    ``Setup`` steps or ``ProcessSetup`` callback sequences.
    """

    ATTACH_TO_SESSION_THEN_CLOSE = 4
    """
    Attach to an existing session. 
    
    When exiting the context manager, automatically close the server session.

    Note: This initialization behavior is intended for TestStand code modules used in
    ``Cleanup`` steps or ``ProcessCleanup`` callback sequences.
    """

"""Session management reservation classes."""

from __future__ import annotations

import abc
import contextlib
import functools
import sys
from contextlib import ExitStack
from functools import cached_property
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from ni_measurementlink_service._drivers import (
    closing_session,
    closing_session_with_ts_code_module_support,
)
from ni_measurementlink_service._featuretoggles import (
    MULTIPLEXER_SUPPORT_2024Q2,
    requires_feature,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool
from ni_measurementlink_service.session_management._constants import (
    INSTRUMENT_TYPE_NI_DAQMX,
    INSTRUMENT_TYPE_NI_DCPOWER,
    INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
    INSTRUMENT_TYPE_NI_DMM,
    INSTRUMENT_TYPE_NI_FGEN,
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    INSTRUMENT_TYPE_NI_SCOPE,
    SITE_SYSTEM_PINS,
)
from ni_measurementlink_service.session_management._types import (
    Connection,
    MultiplexerSessionInformation,
    SessionInformation,
    SessionInitializationBehavior,
    TMultiplexerSession,
    TSession,
    TypedConnection,
    TypedConnectionWithMultiplexer,
    TypedMultiplexerSessionInformation,
    TypedSessionInformation,
)

if TYPE_CHECKING:
    # Driver API packages are optional dependencies, so only import them lazily
    # at run time or when type-checking.
    import nidaqmx
    import nidcpower
    import nidigital
    import nidmm
    import nifgen
    import niscope
    import niswitch

    from ni_measurementlink_service.session_management._client import (  # circular import
        SessionManagementClient,
    )

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

_T = TypeVar("_T")


def _to_iterable(
    value: Union[_T, Iterable[_T], None], default: Optional[Iterable[_T]] = None
) -> Iterable[_T]:
    if value is None:
        return default or []
    elif isinstance(value, Iterable):
        # str implements Iterable[str] for iterating over characters.
        if isinstance(value, str):
            return [cast(_T, value)]
        return value
    else:
        return [value]


# The `dict_view` type is a set-like type. In Python 3.7 and later, dictionaries
# preserve insertion order.
#
# Note: the set difference operator does not preserve order.
def _to_ordered_set(values: Iterable[_T]) -> AbstractSet[_T]:
    return dict.fromkeys(values).keys()


def _quote(value: str) -> str:
    return f"'{value}'"


def _quote_if_str(value: object) -> str:
    return _quote(value) if isinstance(value, str) else str(value)


def _check_optional_str_param(name: str, value: Optional[str]) -> None:
    if value is not None and not isinstance(value, str):
        raise TypeError(f"The {name} parameter must be a str or None, not {value!r}.")


# Why not generic: the error messages differ by "a" vs. "an"
def _check_optional_int_param(name: str, value: Optional[int]) -> None:
    if value is not None and not isinstance(value, int):
        raise TypeError(f"The {name} parameter must be an int or None, not {value!r}.")


def _check_matching_criterion(
    name: str, requested_values: Iterable[_T], expected_values: AbstractSet[_T]
) -> None:
    if not all(value in expected_values for value in requested_values):
        extra_values_str = ", ".join(
            _quote_if_str(value) for value in requested_values if value not in expected_values
        )
        raise ValueError(f"No reserved connections matched {name} {extra_values_str}.")


# Why not generic: the error messages differ by "reserved connection" vs. "multiplexer session"
def _check_matching_multiplexer_criterion(
    name: str, requested_values: Iterable[_T], expected_values: AbstractSet[_T]
) -> None:
    if not all(value in expected_values for value in requested_values):
        extra_values_str = ", ".join(
            _quote_if_str(value) for value in requested_values if value not in expected_values
        )
        raise ValueError(f"No multiplexer sessions matched {name} {extra_values_str}.")


def _describe_matching_criteria(
    pin_or_relay_names: Union[str, Iterable[str], None] = None,
    sites: Union[int, Iterable[int], None] = None,
    instrument_type_id: Optional[str] = None,
) -> str:
    criteria = []
    if pin_or_relay_names is not None:
        pin_or_relay_names = _to_iterable(pin_or_relay_names)
        pin_or_relay_names_str = ", ".join(_quote(pin) for pin in pin_or_relay_names)
        criteria.append(f"pin or relay name(s) {pin_or_relay_names_str}")
    if sites is not None:
        sites = _to_iterable(sites)
        sites_str = ", ".join(str(site) for site in sites)
        criteria.append(f"site(s) {sites_str}")
    if instrument_type_id is not None:
        criteria.append(f"instrument type ID '{instrument_type_id}'")
    return "; ".join(criteria)


class _ConnectionKey(NamedTuple):
    pin_or_relay_name: str
    site: int
    instrument_type_id: str


class _BaseSessionContainer(abc.ABC):
    """Contains session management client and related properties."""

    def __init__(
        self,
        session_management_client: SessionManagementClient,
    ) -> None:
        """Initialize the base session container."""
        self._session_management_client = session_management_client

    @property
    def _discovery_client(self) -> DiscoveryClient:
        if not self._session_management_client._discovery_client:
            raise ValueError("This method requires a discovery client.")
        return self._session_management_client._discovery_client

    @property
    def _grpc_channel_pool(self) -> GrpcChannelPool:
        if not self._session_management_client._grpc_channel_pool:
            raise ValueError("This method requires a gRPC channel pool.")
        return self._session_management_client._grpc_channel_pool


class MultiplexerSessionContainer(_BaseSessionContainer):
    """Manages multiplexer session information."""

    def __init__(
        self,
        session_management_client: SessionManagementClient,
        multiplexer_session_info: Optional[
            Sequence[session_management_service_pb2.MultiplexerSessionInformation]
        ],
    ) -> None:
        """Initialize multiplexer object."""
        super().__init__(session_management_client)
        self._multiplexer_session_cache: Dict[str, object] = {}

        if multiplexer_session_info is not None:
            self._multiplexer_session_info = [
                MultiplexerSessionInformation._from_grpc_v1(info)
                for info in multiplexer_session_info
            ]
        else:
            self._multiplexer_session_info = []

    @cached_property
    def _multiplexer_type_ids(self) -> AbstractSet[str]:
        return _to_ordered_set(
            sorted(info.multiplexer_type_id for info in self._multiplexer_session_info)
        )

    @property
    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def multiplexer_session_info(self) -> Sequence[MultiplexerSessionInformation]:
        """Multiplexer session information object."""
        if not self._multiplexer_session_cache:
            return self._multiplexer_session_info

        return [
            info._with_session(self._multiplexer_session_cache.get(info.session_name))
            for info in self._multiplexer_session_info
        ]

    def __enter__(self: Self) -> Self:
        """Context management protocol. Returns self."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Context management protocol."""
        pass

    def _get_multiplexer_session_info_for_resource_name(
        self, multiplexer_resource_name: str
    ) -> Optional[MultiplexerSessionInformation]:
        return next(
            (
                info
                for info in self._multiplexer_session_info
                if info.resource_name == multiplexer_resource_name
            ),
            None,
        )

    def _get_multiplexer_session_infos_for_type_id(
        self, multiplexer_type_id: str
    ) -> List[MultiplexerSessionInformation]:
        return [
            info
            for info in self._multiplexer_session_info
            if info.multiplexer_type_id == multiplexer_type_id
        ]

    def _validate_and_get_matching_multiplexer_session_infos(
        self,
        multiplexer_type_ids: Iterable[str],
    ) -> List[MultiplexerSessionInformation]:
        if len(self.multiplexer_session_info) == 0:
            raise ValueError(f"No multiplexer sessions available to initialize.")
        _check_matching_multiplexer_criterion(
            "multiplexer type id", multiplexer_type_ids, self._multiplexer_type_ids
        )

        multiplexer_session_infos: List[MultiplexerSessionInformation] = []
        for type_id in multiplexer_type_ids:
            matching_session_info = self._get_multiplexer_session_infos_for_type_id(type_id)
            if matching_session_info:
                multiplexer_session_infos.extend(matching_session_info)
        return multiplexer_session_infos

    @contextlib.contextmanager
    def _cache_multiplexer_session(
        self, session_name: str, session: TMultiplexerSession
    ) -> Generator[None, None, None]:
        if session_name in self._multiplexer_session_cache:
            raise RuntimeError(f"Multiplexer session '{session_name}' already exists.")
        self._multiplexer_session_cache[session_name] = session
        try:
            yield
        finally:
            del self._multiplexer_session_cache[session_name]

    @contextlib.contextmanager
    def _initialize_multiplexer_session_core(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str],
        closing_function: Optional[
            Callable[[TMultiplexerSession], ContextManager[TMultiplexerSession]]
        ] = None,
    ) -> Generator[TypedMultiplexerSessionInformation[TMultiplexerSession], None, None]:
        _check_optional_str_param("multiplexer_type_id", multiplexer_type_id)
        multiplexer_session_infos = self._validate_and_get_matching_multiplexer_session_infos(
            _to_iterable(multiplexer_type_id, self._multiplexer_type_ids),
        )
        if len(multiplexer_session_infos) > 1:
            raise ValueError(
                f"Too many multiplexer sessions matched the specified criteria. "
                f"Expected single multiplexer session, got {len(multiplexer_session_infos)} sessions."
            )

        if closing_function is None:
            closing_function = closing_session

        multiplexer_session_info = multiplexer_session_infos[0]
        with closing_function(session_constructor(multiplexer_session_info)) as session:
            with self._cache_multiplexer_session(multiplexer_session_info.session_name, session):
                new_session_info = multiplexer_session_info._with_session(session)
                yield cast(
                    TypedMultiplexerSessionInformation[TMultiplexerSession], new_session_info
                )

    @contextlib.contextmanager
    def _initialize_multiplexer_sessions_core(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str],
        closing_function: Optional[
            Callable[[TMultiplexerSession], ContextManager[TMultiplexerSession]]
        ] = None,
    ) -> Generator[Sequence[TypedMultiplexerSessionInformation[TMultiplexerSession]], None, None]:
        _check_optional_str_param("multiplexer_type_id", multiplexer_type_id)
        multiplexer_session_infos = self._validate_and_get_matching_multiplexer_session_infos(
            _to_iterable(multiplexer_type_id, self._multiplexer_type_ids),
        )

        if closing_function is None:
            closing_function = closing_session

        multiplexer_session_infos = sorted(
            multiplexer_session_infos, key=lambda x: (x.resource_name)
        )
        with ExitStack() as stack:
            typed_multiplexer_session_infos: List[
                TypedMultiplexerSessionInformation[TMultiplexerSession]
            ] = []
            for multiplexer_session_info in multiplexer_session_infos:
                session = stack.enter_context(
                    closing_function(session_constructor(multiplexer_session_info))
                )
                stack.enter_context(
                    self._cache_multiplexer_session(multiplexer_session_info.session_name, session)
                )
                new_session_info = multiplexer_session_info._with_session(session)
                typed_multiplexer_session_infos.append(
                    cast(TypedMultiplexerSessionInformation[TMultiplexerSession], new_session_info)
                )
            yield typed_multiplexer_session_infos

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_multiplexer_session(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[TypedMultiplexerSessionInformation[TMultiplexerSession]]:
        """Initialize a single multiplexer session.

        This is a generic method that supports any multiplexer driver.

        Args:
            session_constructor: A function that constructs multiplexer sessions
                based on multiplexer session information.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a multiplexer session information
                object. The session object is available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available or
                too many multiplexer sessions are available.
        """
        return self._initialize_multiplexer_session_core(session_constructor, multiplexer_type_id)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_multiplexer_sessions(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[Sequence[TypedMultiplexerSessionInformation[TMultiplexerSession]]]:
        """Initialize multiple multiplexer sessions.

        This is a generic method that supports any multiplexer driver.

        Args:
            session_constructor: A function that constructs multiplexer sessions
                based on multiplexer session information.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a sequence of multiplexer session information
                objects. The session objects are available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available.
        """
        return self._initialize_multiplexer_sessions_core(session_constructor, multiplexer_type_id)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_niswitch_multiplexer_session(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[TypedMultiplexerSessionInformation[niswitch.Session]]:
        """Initialize a single NI-SWITCH multiplexer session.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_MULTIPLEXER_SIMULATE`` in the
                configuration file (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a session information object. The
                multiplexer session object is available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available or
                too many multiplexer sessions are available.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        from ni_measurementlink_service._drivers._niswitch import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            topology,
            simulate,
            reset_device,
            initialization_behavior,
            is_multiplexer=True,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_multiplexer_session_core(
            session_constructor, multiplexer_type_id, closing_function
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_niswitch_multiplexer_sessions(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[Sequence[TypedMultiplexerSessionInformation[niswitch.Session]]]:
        """Initialize multiple NI-SWITCH multiplexer sessions.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_MULTIPLEXER_SIMULATE`` in the
                configuration file (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a sequence of multiplexer session
                information objects. The session objects are available via
                the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        from ni_measurementlink_service._drivers._niswitch import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            topology,
            simulate,
            reset_device,
            initialization_behavior,
            is_multiplexer=True,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_multiplexer_sessions_core(
            session_constructor, multiplexer_type_id, closing_function
        )


class BaseReservation(_BaseSessionContainer):
    """Manages session reservation."""

    def __init__(
        self,
        session_management_client: SessionManagementClient,
        session_info: Sequence[session_management_service_pb2.SessionInformation],
        multiplexer_session_info: Optional[
            Sequence[session_management_service_pb2.MultiplexerSessionInformation]
        ] = None,
        pin_or_relay_group_mappings: Optional[Mapping[str, Iterable[str]]] = None,
        reserved_pin_or_relay_names: Union[str, Iterable[str], None] = None,
        reserved_sites: Optional[Iterable[int]] = None,
    ) -> None:
        """Initialize reservation object."""
        super().__init__(session_management_client)

        self._grpc_session_info = session_info  # required for unreserve
        self._session_info = [
            SessionInformation._from_grpc_v1(info) for info in self._grpc_session_info
        ]
        self._session_cache: Dict[str, object] = {}
        self._multiplexer_session_container = MultiplexerSessionContainer(
            session_management_client, multiplexer_session_info
        )
        self._pin_or_relay_group_mappings: Mapping[str, Iterable[str]] = {}
        if pin_or_relay_group_mappings is not None:
            self._pin_or_relay_group_mappings = pin_or_relay_group_mappings

        # If __init__ doesn't initialize _reserved_pin_or_relay_names or
        # _reserved_sites, the cached properties lazily initialize them.
        if reserved_pin_or_relay_names is not None:
            self._reserved_pin_or_relay_names = _to_ordered_set(
                self._get_resolved_pin_or_relay_names(_to_iterable(reserved_pin_or_relay_names))
            )

        if reserved_sites is not None:
            self._reserved_sites = _to_ordered_set(reserved_sites)

    @cached_property
    def _reserved_pin_or_relay_names(self) -> AbstractSet[str]:
        # If __init__ doesn't initialize reserved_pin_or_relay_names, this
        # cached property initializes it to the pin/relay names listed in the
        # session info (in insertion order, no duplicates).
        return _to_ordered_set(
            channel_mapping.pin_or_relay_name
            for session_info in self._session_info
            for channel_mapping in session_info.channel_mappings
        )

    @cached_property
    def _reserved_sites(self) -> AbstractSet[int]:
        # If __init__ doesn't initialize reserved_sites, this cached property
        # initializes it to the sites listed in the session info (in insertion
        # order, no duplicates).
        return _to_ordered_set(
            channel_mapping.site
            for session_info in self._session_info
            for channel_mapping in session_info.channel_mappings
        )

    @cached_property
    def _reserved_instrument_type_ids(self) -> AbstractSet[str]:
        # Initialize to the instrument type ids listed in the session info (in
        # alphabetical order, no duplicates).
        return _to_ordered_set(
            sorted(session_info.instrument_type_id for session_info in self._session_info)
        )

    @cached_property
    def _connection_cache(self) -> Dict[_ConnectionKey, Connection]:
        cache = {}
        for session_info in self._session_info:
            for channel_mapping in session_info.channel_mappings:
                key = _ConnectionKey(
                    channel_mapping.pin_or_relay_name,
                    channel_mapping.site,
                    session_info.instrument_type_id,
                )
                value = Connection(
                    pin_or_relay_name=channel_mapping.pin_or_relay_name,
                    site=channel_mapping.site,
                    channel_name=channel_mapping.channel,
                    session_info=session_info,
                    multiplexer_resource_name=channel_mapping.multiplexer_resource_name,
                    multiplexer_route=channel_mapping.multiplexer_route,
                    multiplexer_session_info=(
                        self._multiplexer_session_container._get_multiplexer_session_info_for_resource_name(
                            channel_mapping.multiplexer_resource_name
                        )
                    ),
                )
                assert key not in cache
                cache[key] = value
        return cache

    @property
    def _multiplexer_session_cache(self) -> Dict[str, object]:
        return self._multiplexer_session_container._multiplexer_session_cache

    @property
    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def multiplexer_session_info(self) -> Sequence[MultiplexerSessionInformation]:
        """Multiplexer session information object."""
        return self._multiplexer_session_container.multiplexer_session_info

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
        self._session_management_client._unreserve_sessions(self._grpc_session_info)

    @contextlib.contextmanager
    def _cache_session(self, session_name: str, session: TSession) -> Generator[None, None, None]:
        if session_name in self._session_cache:
            raise RuntimeError(f"Session '{session_name}' already exists.")
        self._session_cache[session_name] = session
        try:
            yield
        finally:
            del self._session_cache[session_name]

    def _get_matching_session_infos(self, instrument_type_id: str) -> List[SessionInformation]:
        return [
            info for info in self._session_info if instrument_type_id == info.instrument_type_id
        ]

    def _get_resolved_pin_or_relay_names(
        self, reserved_pin_or_relay_names: Iterable[str]
    ) -> Iterable[str]:
        resolved_pin_or_relay_names: List[str] = []
        for pin_or_relay_name in reserved_pin_or_relay_names:
            if pin_or_relay_name in self._pin_or_relay_group_mappings:
                resolved_pin_or_relay_names.extend(
                    self._pin_or_relay_group_mappings[pin_or_relay_name]
                )
            else:
                resolved_pin_or_relay_names.append(pin_or_relay_name)

        return resolved_pin_or_relay_names

    @contextlib.contextmanager
    def _initialize_session_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
        closing_function: Optional[Callable[[TSession], ContextManager[TSession]]] = None,
    ) -> Generator[TypedSessionInformation[TSession], None, None]:
        if not instrument_type_id:
            raise ValueError("This method requires an instrument type ID.")
        session_infos = self._get_matching_session_infos(instrument_type_id)
        if len(session_infos) == 0:
            raise ValueError(
                f"No reserved sessions matched instrument type ID '{instrument_type_id}'. "
                "Expected single session, got 0 sessions."
            )
        elif len(session_infos) > 1:
            raise ValueError(
                f"Too many reserved sessions matched instrument type ID '{instrument_type_id}'. "
                f"Expected single session, got {len(session_infos)} sessions."
            )

        if closing_function is None:
            closing_function = closing_session

        session_info = session_infos[0]
        with closing_function(session_constructor(session_info)) as session:
            with self._cache_session(session_info.session_name, session):
                new_session_info = session_info._with_session(session)
                yield cast(TypedSessionInformation[TSession], new_session_info)

    @contextlib.contextmanager
    def _initialize_sessions_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
        closing_function: Optional[Callable[[TSession], ContextManager[TSession]]] = None,
    ) -> Generator[Sequence[TypedSessionInformation[TSession]], None, None]:
        if not instrument_type_id:
            raise ValueError("This method requires an instrument type ID.")
        session_infos = self._get_matching_session_infos(instrument_type_id)
        if len(session_infos) == 0:
            raise ValueError(
                f"No reserved sessions matched instrument type ID '{instrument_type_id}'. "
                "Expected single or multiple sessions, got 0 sessions."
            )

        if closing_function is None:
            closing_function = closing_session

        with ExitStack() as stack:
            typed_session_infos: List[TypedSessionInformation[TSession]] = []
            for session_info in session_infos:
                session = stack.enter_context(closing_function(session_constructor(session_info)))
                stack.enter_context(self._cache_session(session_info.session_name, session))
                new_session_info = session_info._with_session(session)
                typed_session_infos.append(
                    cast(TypedSessionInformation[TSession], new_session_info)
                )
            yield typed_session_infos

    def _get_connection_core(
        self,
        session_type: Type[TSession],
        pin_or_relay_name: Optional[str] = None,
        site: Optional[int] = None,
        instrument_type_id: Optional[str] = None,
        multiplexer_session_type: Optional[Type[TMultiplexerSession]] = None,
    ) -> TypedConnection[TSession]:
        _check_optional_str_param("pin_or_relay_name", pin_or_relay_name)
        _check_optional_int_param("site", site)
        # _get_connections_core() checks instrument_type_id.

        results = self._get_connections_core(
            session_type, pin_or_relay_name, site, instrument_type_id, multiplexer_session_type
        )

        if not results:
            raise ValueError(
                "No reserved connections matched the specified criteria. "
                "Expected single connection, got 0 connections."
            )
        elif len(results) > 1:
            raise ValueError(
                "Too many reserved connections matched the specified criteria. "
                f"Expected single connection, got {len(results)} connections."
            )

        return results[0]

    def _get_connections_core(
        self,
        session_type: Type[TSession],
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
        instrument_type_id: Optional[str] = None,
        multiplexer_session_type: Optional[Type[TMultiplexerSession]] = None,
    ) -> Sequence[TypedConnection[TSession]]:
        _check_optional_str_param("instrument_type_id", instrument_type_id)

        requested_pin_or_relay_names = _to_iterable(
            pin_or_relay_names, self._reserved_pin_or_relay_names
        )
        requested_sites = _to_iterable(sites, self._reserved_sites)
        requested_instrument_type_ids = _to_iterable(
            instrument_type_id, self._reserved_instrument_type_ids
        )

        resolved_pin_or_relay_names = _to_ordered_set(
            self._get_resolved_pin_or_relay_names(requested_pin_or_relay_names)
        )

        # Validate that each requested pin, site, or instrument type ID is
        # present in the reserved pins, reserved sites, and reserved instrument
        # type IDs. This rejects unknown or invalid inputs such as
        # pin_or_relay_names="NonExistentPin" or sites=[0, 1, 65535].
        if pin_or_relay_names is not None:
            _check_matching_criterion(
                "pin or relay name(s)",
                resolved_pin_or_relay_names,
                self._reserved_pin_or_relay_names,
            )
        if sites is not None:
            _check_matching_criterion("site(s)", requested_sites, self._reserved_sites)
        if instrument_type_id is not None:
            _check_matching_criterion(
                "instrument type ID",
                requested_instrument_type_ids,
                self._reserved_instrument_type_ids,
            )

        requested_sites_with_system = requested_sites
        if SITE_SYSTEM_PINS not in requested_sites_with_system:
            requested_sites_with_system = list(requested_sites_with_system)
            requested_sites_with_system.append(SITE_SYSTEM_PINS)

        # Sort the results by site, then by pin, then by instrument type (as a tiebreaker).
        results: List[TypedConnection[TSession]] = []
        matching_pins: Set[str] = set()
        for site in requested_sites_with_system:
            for pin in resolved_pin_or_relay_names:
                for instrument_type in requested_instrument_type_ids:
                    key = _ConnectionKey(pin, site, instrument_type)
                    value = self._connection_cache.get(key)
                    if value is not None:
                        session = self._session_cache.get(value.session_info.session_name)
                        value = value._with_session(session)
                        value._check_runtime_type(session_type)
                        if multiplexer_session_type is not None:
                            if value.multiplexer_session_info is not None:
                                multiplexer_session = self._multiplexer_session_cache.get(
                                    value.multiplexer_session_info.session_name
                                )
                                value = value._with_multiplexer_session(multiplexer_session)
                            value._check_runtime_multiplexer_type(multiplexer_session_type)
                        results.append(cast(TypedConnection[TSession], value))
                        matching_pins.add(pin)

        # If the user specified pins to match, validate that each one matched a connection.
        if pin_or_relay_names is not None and not all(
            pin in matching_pins for pin in resolved_pin_or_relay_names
        ):
            extra_pins_str = ", ".join(
                _quote(pin) for pin in resolved_pin_or_relay_names if pin not in matching_pins
            )
            criteria = _describe_matching_criteria(None, sites, instrument_type_id)
            # Emphasize the extra pin/relay names, but also list the other criteria.
            raise ValueError(
                f"No reserved connections matched pin or relay name(s) {extra_pins_str} "
                f"with the specified criteria: {criteria}"
            )

        # If the user specified any matching criteria, validate that matches
        # were found.
        if (pin_or_relay_names or sites or instrument_type_id) is not None and not results:
            criteria = _describe_matching_criteria(pin_or_relay_names, sites, instrument_type_id)
            raise ValueError(f"No reserved connections matched the specified criteria: {criteria}")

        return results

    def initialize_session(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> ContextManager[TypedSessionInformation[TSession]]:
        """Initialize a single instrument session.

        This is a generic method that supports any instrument driver.

        Args:
            session_constructor: A function that constructs sessions based on
                session information.

            instrument_type_id: Instrument type ID for the session.

                For custom instruments, use the instrument type id defined in
                the pin map file.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If the instrument type ID is empty, no reserved sessions
                match the instrument type ID, or too many reserved sessions
                match the instrument type ID.
        """
        return self._initialize_session_core(session_constructor, instrument_type_id)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_multiplexer_session(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[TypedMultiplexerSessionInformation[TMultiplexerSession]]:
        """Initialize a single multiplexer session.

        This is a generic method that supports any multiplexer driver.

        Args:
            session_constructor: A function that constructs multiplexer sessions
                based on multiplexer session information.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a multiplexer session information
                object. The session object is available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available or
                too many multiplexer sessions are available.
        """
        return self._multiplexer_session_container.initialize_multiplexer_session(
            session_constructor, multiplexer_type_id
        )

    def initialize_sessions(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> ContextManager[Sequence[TypedSessionInformation[TSession]]]:
        """Initialize multiple instrument sessions.

        This is a generic method that supports any instrument driver.

        Args:
            session_constructor: A function that constructs sessions based on
                session information.

            instrument_type_id: Instrument type ID for the session.

                For custom instruments, use the instrument type id defined in
                the pin map file.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If the instrument type ID is empty or no reserved
                sessions matched the instrument type ID.
        """
        return self._initialize_sessions_core(session_constructor, instrument_type_id)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_multiplexer_sessions(
        self,
        session_constructor: Callable[[MultiplexerSessionInformation], TMultiplexerSession],
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[Sequence[TypedMultiplexerSessionInformation[TMultiplexerSession]]]:
        """Initialize multiple multiplexer sessions.

        This is a generic method that supports any multiplexer driver.

        Args:
            session_constructor: A function that constructs multiplexer sessions
                based on multiplexer session information.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a sequence of multiplexer session information
                objects. The session objects are available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available.
        """
        return self._multiplexer_session_container.initialize_multiplexer_sessions(
            session_constructor, multiplexer_type_id
        )

    def get_connection(
        self,
        session_type: Type[TSession],
        pin_or_relay_name: Optional[str] = None,
        site: Optional[int] = None,
        instrument_type_id: Optional[str] = None,
    ) -> TypedConnection[TSession]:
        """Get the connection matching the specified criteria.

        This is a generic method that supports any instrument driver.

        Args:
            session_type: The session type.

            pin_or_relay_name: The pin or relay name to match against. If not
                specified, the pin or relay name is ignored when matching
                connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

            instrument_type_id: The instrument type ID to match against. If not
                specified, the instrument type ID is ignored when matching
                connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        return self._get_connection_core(session_type, pin_or_relay_name, site, instrument_type_id)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_connection_with_multiplexer(
        self,
        session_type: Type[TSession],
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_or_relay_name: Optional[str] = None,
        site: Optional[int] = None,
        instrument_type_id: Optional[str] = None,
    ) -> TypedConnectionWithMultiplexer[TSession, TMultiplexerSession]:
        """Get the connection matching the specified criteria.

        This is a generic method that supports any instrument driver.

        Args:
            session_type: The instrument session type.

            multiplexer_session_type: The multiplexer session type.

            pin_or_relay_name: The pin or relay name to match against. If not
                specified, the pin or relay name is ignored when matching
                connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

            instrument_type_id: The instrument type ID to match against. If not
                specified, the instrument type ID is ignored when matching
                connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        connection = self._get_connection_core(
            session_type, pin_or_relay_name, site, instrument_type_id, multiplexer_session_type
        )
        return cast(TypedConnectionWithMultiplexer[TSession, TMultiplexerSession], connection)

    def get_connections(
        self,
        session_type: Type[TSession],
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
        instrument_type_id: Optional[str] = None,
    ) -> Sequence[TypedConnection[TSession]]:
        """Get all connections matching the specified criteria.

        This is a generic method that supports any instrument driver.

        Args:
            session_type: The expected session type.

            pin_or_relay_names: The pin or relay name(s) to match against. If
                not specified, the pin or relay name is ignored when matching
                connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

            instrument_type_id: The instrument type ID to match against. If not
                specified, the instrument type ID is ignored when matching
                connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        return self._get_connections_core(
            session_type, pin_or_relay_names, sites, instrument_type_id
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_connections_with_multiplexer(
        self,
        session_type: Type[TSession],
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_or_relay_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
        instrument_type_id: Optional[str] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[TSession, TMultiplexerSession]]:
        """Get all connections matching the specified criteria.

        This is a generic method that supports any instrument driver.

        Args:
            session_type: The instrument session type.

            multiplexer_session_type: The multiplexer session type.

            pin_or_relay_names: The pin or relay name(s) to match against. If
                not specified, the pin or relay name is ignored when matching
                connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

            instrument_type_id: The instrument type ID to match against. If not
                specified, the instrument type ID is ignored when matching
                connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        connections = self._get_connections_core(
            session_type, pin_or_relay_names, sites, instrument_type_id, multiplexer_session_type
        )
        return [
            cast(TypedConnectionWithMultiplexer[TSession, TMultiplexerSession], conn)
            for conn in connections
        ]

    def create_nidaqmx_task(
        self,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidaqmx.Task]]:
        """Create a single NI-DAQmx task.

        Args:
            initialization_behavior: Specifies whether the NI gRPC Device Server
                will create a new task or attach to an existing task.

        Returns:
            A context manager that yields a session information object. The task
            object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-DAQmx tasks are reserved or too many
                NI-DAQmx tasks are reserved.

        Note:
            If the ``session_exists`` field is ``False``, the returned task is
            empty and the caller is expected to add channels to it.

        See Also:
            For more details, see :py:class:`nidaqmx.Task`.
        """
        from ni_measurementlink_service._drivers._nidaqmx import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client, self._grpc_channel_pool, initialization_behavior
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_DAQMX, closing_function
        )

    def create_nidaqmx_tasks(
        self,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidaqmx.Task]]]:
        """Create multiple NI-DAQmx tasks.

        Args:
            initialization_behavior: Specifies whether the NI gRPC Device Server
                will create a new task or attach to an existing task.

        Returns:
            A context manager that yields a sequence of session information
            objects. The task objects are available via the ``session`` field.

        Raises:
            ValueError: If no NI-DAQmx tasks are reserved.

        Note:
            If the ``session_exists`` field is ``False``, the returned tasks are
            empty and the caller is expected to add channels to them.

        See Also:
            For more details, see :py:class:`nidaqmx.Task`.
        """
        from ni_measurementlink_service._drivers._nidaqmx import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client, self._grpc_channel_pool, initialization_behavior
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_DAQMX, closing_function
        )

    def get_nidaqmx_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[nidaqmx.Task]:
        """Get the NI-DAQmx connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidaqmx

        return self._get_connection_core(nidaqmx.Task, pin_name, site, INSTRUMENT_TYPE_NI_DAQMX)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidaqmx_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[nidaqmx.Task, TMultiplexerSession]:
        """Get the NI-DAQmx connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidaqmx

        connection = self._get_connection_core(
            nidaqmx.Task, pin_name, site, INSTRUMENT_TYPE_NI_DAQMX, multiplexer_session_type
        )
        return cast(TypedConnectionWithMultiplexer[nidaqmx.Task, TMultiplexerSession], connection)

    def get_nidaqmx_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[nidaqmx.Task]]:
        """Get all NI-DAQmx connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidaqmx

        return self._get_connections_core(nidaqmx.Task, pin_names, sites, INSTRUMENT_TYPE_NI_DAQMX)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidaqmx_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[nidaqmx.Task, TMultiplexerSession]]:
        """Get all NI-DAQmx connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidaqmx

        connections = self._get_connections_core(
            nidaqmx.Task, pin_names, sites, INSTRUMENT_TYPE_NI_DAQMX, multiplexer_session_type
        )
        return [
            cast(TypedConnectionWithMultiplexer[nidaqmx.Task, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_nidcpower_session(
        self,
        reset: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidcpower.Session]]:
        """Initialize a single NI-DCPower instrument session.

        Args:
            reset: Specifies whether to reset channel(s) during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDCPOWER_SIMULATE``, ``NIDCPOWER_BOARD_TYPE``, and
                ``NIDCPOWER_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-DCPower sessions are reserved or too many
                NI-DCPower sessions are reserved.

        See Also:
            For more details, see :py:class:`nidcpower.Session`.
        """
        from ni_measurementlink_service._drivers._nidcpower import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client, self._grpc_channel_pool, reset, options, initialization_behavior
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_DCPOWER, closing_function
        )

    def initialize_nidcpower_sessions(
        self,
        reset: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidcpower.Session]]]:
        """Initialize multiple NI-DCPower instrument sessions.

        Args:
            reset: Specifies whether to reset channel(s) during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDCPOWER_SIMULATE``, ``NIDCPOWER_BOARD_TYPE``, and
                ``NIDCPOWER_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no NI-DCPower sessions are reserved.

        See Also:
            For more details, see :py:class:`nidcpower.Session`.
        """
        from ni_measurementlink_service._drivers._nidcpower import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client, self._grpc_channel_pool, reset, options, initialization_behavior
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_DCPOWER, closing_function
        )

    def get_nidcpower_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[nidcpower.Session]:
        """Get the NI-DCPower connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidcpower

        return self._get_connection_core(
            nidcpower.Session, pin_name, site, INSTRUMENT_TYPE_NI_DCPOWER
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidcpower_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[nidcpower.Session, TMultiplexerSession]:
        """Get the NI-DCPower connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidcpower

        connection = self._get_connection_core(
            nidcpower.Session, pin_name, site, INSTRUMENT_TYPE_NI_DCPOWER, multiplexer_session_type
        )
        return cast(
            TypedConnectionWithMultiplexer[nidcpower.Session, TMultiplexerSession], connection
        )

    def get_nidcpower_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[nidcpower.Session]]:
        """Get all NI-DCPower connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidcpower

        return self._get_connections_core(
            nidcpower.Session, pin_names, sites, INSTRUMENT_TYPE_NI_DCPOWER
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidcpower_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[nidcpower.Session, TMultiplexerSession]]:
        """Get all NI-DCPower connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidcpower

        connections = self._get_connections_core(
            nidcpower.Session,
            pin_names,
            sites,
            INSTRUMENT_TYPE_NI_DCPOWER,
            multiplexer_session_type,
        )
        return [
            cast(TypedConnectionWithMultiplexer[nidcpower.Session, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_nidigital_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidigital.Session]]:
        """Initialize a single NI-Digital Pattern instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDIGITAL_SIMULATE``, ``NIDIGITAL_BOARD_TYPE``, and
                ``NIDIGITAL_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-Digital sessions are reserved or too many
                NI-Digital sessions are reserved.

        See Also:
            For more details, see :py:class:`nidigital.Session`.
        """
        from ni_measurementlink_service._drivers._nidigital import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN, closing_function
        )

    def initialize_nidigital_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidigital.Session]]]:
        """Initialize multiple NI-Digital Pattern instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDIGITAL_SIMULATE``, ``NIDIGITAL_BOARD_TYPE``, and
                ``NIDIGITAL_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no NI-Digital sessions are reserved.

        See Also:
            For more details, see :py:class:`nidigital.Session`.
        """
        from ni_measurementlink_service._drivers._nidigital import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN, closing_function
        )

    def get_nidigital_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[nidigital.Session]:
        """Get the NI-Digital Pattern connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidigital

        return self._get_connection_core(
            nidigital.Session, pin_name, site, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidigital_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[nidigital.Session, TMultiplexerSession]:
        """Get the NI-Digital Pattern connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidigital

        connection = self._get_connection_core(
            nidigital.Session,
            pin_name,
            site,
            INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
            multiplexer_session_type,
        )
        return cast(
            TypedConnectionWithMultiplexer[nidigital.Session, TMultiplexerSession], connection
        )

    def get_nidigital_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[nidigital.Session]]:
        """Get all NI-Digital Pattern connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidigital

        return self._get_connections_core(
            nidigital.Session, pin_names, sites, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidigital_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[nidigital.Session, TMultiplexerSession]]:
        """Get all NI-Digital Pattern connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidigital

        connections = self._get_connections_core(
            nidigital.Session,
            pin_names,
            sites,
            INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
            multiplexer_session_type,
        )
        return [
            cast(TypedConnectionWithMultiplexer[nidigital.Session, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_nidmm_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidmm.Session]]:
        """Initialize a single NI-DMM instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDMM_SIMULATE``, ``NIDMM_BOARD_TYPE``, and ``NIDMM_MODEL`` in
                the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-DMM sessions are reserved or too many
                NI-DMM sessions are reserved.

        See Also:
            For more details, see :py:class:`nidmm.Session`.
        """
        from ni_measurementlink_service._drivers._nidmm import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_DMM, closing_function
        )

    def initialize_nidmm_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidmm.Session]]]:
        """Initialize multiple NI-DMM instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDMM_SIMULATE``, ``NIDMM_BOARD_TYPE``, and ``NIDMM_MODEL`` in
                the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no NI-DMM sessions are reserved.

        See Also:
            For more details, see :py:class:`nidmm.Session`.
        """
        from ni_measurementlink_service._drivers._nidmm import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_DMM, closing_function
        )

    def get_nidmm_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[nidmm.Session]:
        """Get the NI-DMM connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidmm

        return self._get_connection_core(nidmm.Session, pin_name, site, INSTRUMENT_TYPE_NI_DMM)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidmm_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[nidmm.Session, TMultiplexerSession]:
        """Get the NI-DMM connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nidmm

        connection = self._get_connection_core(
            nidmm.Session, pin_name, site, INSTRUMENT_TYPE_NI_DMM, multiplexer_session_type
        )
        return cast(TypedConnectionWithMultiplexer[nidmm.Session, TMultiplexerSession], connection)

    def get_nidmm_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[nidmm.Session]]:
        """Get all NI-DMM connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidmm

        return self._get_connections_core(nidmm.Session, pin_names, sites, INSTRUMENT_TYPE_NI_DMM)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nidmm_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[nidmm.Session, TMultiplexerSession]]:
        """Get all NI-DMM connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nidmm

        connections = self._get_connections_core(
            nidmm.Session, pin_names, sites, INSTRUMENT_TYPE_NI_DMM, multiplexer_session_type
        )
        return [
            cast(TypedConnectionWithMultiplexer[nidmm.Session, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_nifgen_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nifgen.Session]]:
        """Initialize a single NI-FGEN instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIFGEN_SIMULATE``, ``NIFGEN_BOARD_TYPE``, and ``NIFGEN_MODEL``
                in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-FGEN sessions are reserved or too many NI-FGEN
                sessions are reserved.

        See Also:
            For more details, see :py:class:`nifgen.Session`.
        """
        from ni_measurementlink_service._drivers._nifgen import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_FGEN, closing_function
        )

    def initialize_nifgen_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nifgen.Session]]]:
        """Initialize multiple NI-FGEN instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIFGEN_SIMULATE``, ``NIFGEN_BOARD_TYPE``, and ``NIFGEN_MODEL``
                in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no NI-FGEN sessions are reserved.

        See Also:
            For more details, see :py:class:`nifgen.Session`.
        """
        from ni_measurementlink_service._drivers._nifgen import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_FGEN, closing_function
        )

    def get_nifgen_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[nifgen.Session]:
        """Get the NI-FGEN connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nifgen

        return self._get_connection_core(nifgen.Session, pin_name, site, INSTRUMENT_TYPE_NI_FGEN)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nifgen_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[nifgen.Session, TMultiplexerSession]:
        """Get the NI-FGEN connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import nifgen

        connection = self._get_connection_core(
            nifgen.Session, pin_name, site, INSTRUMENT_TYPE_NI_FGEN, multiplexer_session_type
        )
        return cast(TypedConnectionWithMultiplexer[nifgen.Session, TMultiplexerSession], connection)

    def get_nifgen_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[nifgen.Session]]:
        """Get all NI-FGEN connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nifgen

        return self._get_connections_core(nifgen.Session, pin_names, sites, INSTRUMENT_TYPE_NI_FGEN)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_nifgen_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[nifgen.Session, TMultiplexerSession]]:
        """Get all NI-FGEN connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import nifgen

        connections = self._get_connections_core(
            nifgen.Session, pin_names, sites, INSTRUMENT_TYPE_NI_FGEN, multiplexer_session_type
        )
        return [
            cast(TypedConnectionWithMultiplexer[nifgen.Session, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_niscope_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[niscope.Session]]:
        """Initialize a single NI-SCOPE instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NISCOPE_SIMULATE``, ``NISCOPE_BOARD_TYPE``, and
                ``NISCOPE_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no NI-SCOPE sessions are reserved or too many
                NI-SCOPE sessions are reserved.

        See Also:
            For more details, see :py:class:`niscope.Session`.
        """
        from ni_measurementlink_service._drivers._niscope import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_SCOPE, closing_function
        )

    def initialize_niscope_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[niscope.Session]]]:
        """Initialize multiple NI-SCOPE instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NISCOPE_SIMULATE``, ``NISCOPE_BOARD_TYPE``, and
                ``NISCOPE_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no NI-SCOPE sessions are reserved.

        See Also:
            For more details, see :py:class:`niscope.Session`.
        """
        from ni_measurementlink_service._drivers._niscope import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            reset_device,
            options,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_SCOPE, closing_function
        )

    def get_niscope_connection(
        self,
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[niscope.Session]:
        """Get the NI-SCOPE connection matching the specified criteria.

        Args:
            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import niscope

        return self._get_connection_core(niscope.Session, pin_name, site, INSTRUMENT_TYPE_NI_SCOPE)

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_niscope_connection_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnectionWithMultiplexer[niscope.Session, TMultiplexerSession]:
        """Get the NI-SCOPE connection matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_name: The pin name to match against. If not specified, the pin
                name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection along with its multiplexer info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import niscope

        connection = self._get_connection_core(
            niscope.Session, pin_name, site, INSTRUMENT_TYPE_NI_SCOPE, multiplexer_session_type
        )
        return cast(
            TypedConnectionWithMultiplexer[niscope.Session, TMultiplexerSession], connection
        )

    def get_niscope_connections(
        self,
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[niscope.Session]]:
        """Get all NI-SCOPE connections matching the specified criteria.

        Args:
            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import niscope

        return self._get_connections_core(
            niscope.Session, pin_names, sites, INSTRUMENT_TYPE_NI_SCOPE
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def get_niscope_connections_with_multiplexer(
        self,
        multiplexer_session_type: Type[TMultiplexerSession],
        pin_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnectionWithMultiplexer[niscope.Session, TMultiplexerSession]]:
        """Get all NI-SCOPE connections matching the specified criteria.

        Args:
            multiplexer_session_type: The multiplexer session type.

            pin_names: The pin name(s) to match against. If not specified, the
                pin name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections along with their multiplexer(s) info.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import niscope

        connections = self._get_connections_core(
            niscope.Session, pin_names, sites, INSTRUMENT_TYPE_NI_SCOPE, multiplexer_session_type
        )
        return [
            cast(TypedConnectionWithMultiplexer[niscope.Session, TMultiplexerSession], conn)
            for conn in connections
        ]

    def initialize_niswitch_session(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[niswitch.Session]]:
        """Initialize a single NI-SWITCH relay driver instrument session.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_SIMULATE`` in the configuration file
                (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            session object is available via the ``session`` field.

        Raises:
            ValueError: If no relay driver sessions are reserved or
                too many relay driver sessions are reserved.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        from ni_measurementlink_service._drivers._niswitch import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            topology,
            simulate,
            reset_device,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_session_core(
            session_constructor, INSTRUMENT_TYPE_NI_RELAY_DRIVER, closing_function
        )

    def initialize_niswitch_sessions(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[niswitch.Session]]]:
        """Initialize multiple NI-SWITCH relay driver instrument sessions.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_SIMULATE`` in the configuration file
                (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The session objects are available via the ``session``
            field.

        Raises:
            ValueError: If no relay driver sessions are reserved.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        from ni_measurementlink_service._drivers._niswitch import SessionConstructor

        session_constructor = SessionConstructor(
            self._discovery_client,
            self._grpc_channel_pool,
            topology,
            simulate,
            reset_device,
            initialization_behavior,
        )
        closing_function = functools.partial(
            closing_session_with_ts_code_module_support, initialization_behavior
        )
        return self._initialize_sessions_core(
            session_constructor, INSTRUMENT_TYPE_NI_RELAY_DRIVER, closing_function
        )

    def get_niswitch_connection(
        self,
        relay_name: Optional[str] = None,
        site: Optional[int] = None,
    ) -> TypedConnection[niswitch.Session]:
        """Get the NI-SWITCH relay driver connection matching the specified criteria.

        Args:
            relay_name: The relay name to match against. If not specified, the
                relay name is ignored when matching connections.

            site: The site number to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connection.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match or too many reserved
                connections match.
        """
        import niswitch

        return self._get_connection_core(
            niswitch.Session, relay_name, site, INSTRUMENT_TYPE_NI_RELAY_DRIVER
        )

    def get_niswitch_connections(
        self,
        relay_names: Union[str, Iterable[str], None] = None,
        sites: Union[int, Iterable[int], None] = None,
    ) -> Sequence[TypedConnection[niswitch.Session]]:
        """Get all NI-SWITCH relay driver connections matching the specified criteria.

        Args:
            relay_names: The relay name(s) to match against. If not specified,
                the relay name is ignored when matching connections.

            sites: The site number(s) to match against. If not specified, the
                site number is ignored when matching connections.

        Returns:
            The matching connections.

        Raises:
            TypeError: If the argument types or session type are incorrect.

            ValueError: If no reserved connections match.
        """
        import niswitch

        return self._get_connections_core(
            niswitch.Session, relay_names, sites, INSTRUMENT_TYPE_NI_RELAY_DRIVER
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_niswitch_multiplexer_session(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[TypedMultiplexerSessionInformation[niswitch.Session]]:
        """Initialize a single NI-SWITCH multiplexer session.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_SIMULATE`` in the configuration file
                (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a session information object. The
                multiplexer session object is available via the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available or
                too many multiplexer sessions are available.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        return self._multiplexer_session_container.initialize_niswitch_multiplexer_session(
            topology, simulate, reset_device, initialization_behavior, multiplexer_type_id
        )

    @requires_feature(MULTIPLEXER_SUPPORT_2024Q2)
    def initialize_niswitch_multiplexer_sessions(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        multiplexer_type_id: Optional[str] = None,
    ) -> ContextManager[Sequence[TypedMultiplexerSessionInformation[niswitch.Session]]]:
        """Initialize multiple NI-SWITCH multiplexer sessions.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``MEASUREMENTLINK_NISWITCH_TOPOLOGY`` in
                the configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting
                ``MEASUREMENTLINK_NISWITCH_SIMULATE`` in the configuration file
                (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether the NI gRPC Device Server
                will initialize a new session or attach to an existing session.

            multiplexer_type_id: User-defined identifier for the multiplexer
                type in the pin map editor. If not specified, the multiplexer
                type id is ignored when matching multiplexer sessions.

        Returns:
            A context manager that yields a sequence of multiplexer session
                information objects. The session objects are available via
                the ``session`` field.

        Raises:
            TypeError: If the argument types are incorrect.

            ValueError: If no multiplexer sessions are available.

        See Also:
            For more details, see :py:class:`niswitch.Session`.
        """
        return self._multiplexer_session_container.initialize_niswitch_multiplexer_sessions(
            topology, simulate, reset_device, initialization_behavior, multiplexer_type_id
        )


class SingleSessionReservation(BaseReservation):
    """Manages reservation for a single session."""

    @property
    def session_info(self) -> SessionInformation:
        """Single session information object."""
        assert len(self._session_info) == 1
        info = self._session_info[0]
        return info._with_session(self._session_cache.get(info.session_name))


class MultiSessionReservation(BaseReservation):
    """Manages reservation for multiple sessions."""

    @property
    def session_info(self) -> List[SessionInformation]:
        """Multiple session information objects."""
        # If the session cache is empty, return the existing list without copying.
        if not self._session_cache:
            return self._session_info

        return [
            info._with_session(self._session_cache.get(info.session_name))
            for info in self._session_info
        ]

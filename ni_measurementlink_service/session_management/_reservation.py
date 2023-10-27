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
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._drivers import (
    closing_session,
    closing_session_with_ts_code_module_support,
)
from ni_measurementlink_service._featuretoggles import (
    SESSION_MANAGEMENT_2024Q1,
    requires_feature,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.sessionmanagement.v1 import (
    session_management_service_pb2,
)
from ni_measurementlink_service.discovery import DiscoveryClient
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
    SessionInformation,
    SessionInitializationBehavior,
    TSession,
    TypedConnection,
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


class BaseReservation(abc.ABC):
    """Manages session reservation."""

    def __init__(
        self,
        session_manager: SessionManagementClient,
        session_info: Sequence[session_management_service_pb2.SessionInformation],
        reserved_pin_or_relay_names: Union[str, Iterable[str], None] = None,
        reserved_sites: Optional[Iterable[int]] = None,
    ) -> None:
        """Initialize reservation object."""
        self._session_manager = session_manager
        self._grpc_session_info = session_info  # needed for unreserve
        self._session_info = [
            SessionInformation._from_grpc_v1(info) for info in self._grpc_session_info
        ]
        self._session_cache: Dict[str, object] = {}

        # If __init__ doesn't initialize _reserved_pin_or_relay_names or
        # _reserved_sites, the cached properties lazily initialize them.
        if reserved_pin_or_relay_names is not None:
            self._reserved_pin_or_relay_names = _to_ordered_set(
                _to_iterable(reserved_pin_or_relay_names)
            )

        if reserved_sites is not None:
            self._reserved_sites = _to_ordered_set(reserved_sites)

    @property
    def _discovery_client(self) -> DiscoveryClient:
        if not self._session_manager._discovery_client:
            raise ValueError("This method requires a discovery client.")
        return self._session_manager._discovery_client

    @property
    def _grpc_channel_pool(self) -> GrpcChannelPool:
        if not self._session_manager._grpc_channel_pool:
            raise ValueError("This method requires a gRPC channel pool.")
        return self._session_manager._grpc_channel_pool

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
                    channel_mapping.pin_or_relay_name,
                    channel_mapping.site,
                    channel_mapping.channel,
                    session_info,
                )
                assert key not in cache
                cache[key] = value
        return cache

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
        self._session_manager._unreserve_sessions(self._grpc_session_info)

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
    ) -> TypedConnection[TSession]:
        _check_optional_str_param("pin_or_relay_name", pin_or_relay_name)
        _check_optional_int_param("site", site)
        # _get_connections_core() checks instrument_type_id.

        results = self._get_connections_core(
            session_type, pin_or_relay_name, site, instrument_type_id
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
    ) -> Sequence[TypedConnection[TSession]]:
        _check_optional_str_param("instrument_type_id", instrument_type_id)

        requested_pins = _to_iterable(pin_or_relay_names, self._reserved_pin_or_relay_names)
        requested_sites = _to_iterable(sites, self._reserved_sites)
        requested_instrument_type_ids = _to_iterable(
            instrument_type_id, self._reserved_instrument_type_ids
        )

        # Validate that each requested pin, site, or instrument type ID is
        # present in the reserved pins, reserved sites, and reserved instrument
        # type IDs. This rejects unknown or invalid inputs such as
        # pin_or_relay_names="NonExistentPin" or sites=[0, 1, 65535].
        if pin_or_relay_names is not None:
            _check_matching_criterion(
                "pin or relay name(s)", requested_pins, self._reserved_pin_or_relay_names
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
            for pin in requested_pins:
                for instrument_type in requested_instrument_type_ids:
                    key = _ConnectionKey(pin, site, instrument_type)
                    value = self._connection_cache.get(key)
                    if value is not None:
                        session = self._session_cache.get(value.session_info.session_name)
                        value = value._with_session(session)
                        value._check_runtime_type(session_type)
                        results.append(cast(TypedConnection[TSession], value))
                        matching_pins.add(pin)

        # If the user specified pins to match, validate that each one matched a connection.
        if pin_or_relay_names is not None and not all(
            pin in matching_pins for pin in requested_pins
        ):
            extra_pins_str = ", ".join(
                _quote(pin) for pin in requested_pins if pin not in matching_pins
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidaqmx_tasks(
        self,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidcpower.Session]]]:
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
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

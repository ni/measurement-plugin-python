"""Session management reservation classes."""
from __future__ import annotations

import abc
import contextlib
import sys
from contextlib import ExitStack
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    cast,
)

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._drivers import closing_session
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
)
from ni_measurementlink_service.session_management._types import (
    SessionInformation,
    SessionInitializationBehavior,
    TSession,
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


class BaseReservation(abc.ABC):
    """Manages session reservation."""

    def __init__(
        self,
        session_manager: SessionManagementClient,
        session_info: Sequence[session_management_service_pb2.SessionInformation],
    ) -> None:
        """Initialize reservation object."""
        self._session_manager = session_manager
        self._grpc_session_info = session_info  # needed for unreserve
        self._session_info = [
            SessionInformation._from_grpc_v1(info) for info in self._grpc_session_info
        ]
        self._session_cache: Dict[str, object] = {}

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
            info._with_session(self._session_cache.get(info.session_name))
            for info in self._session_info
            if instrument_type_id and instrument_type_id == info.instrument_type_id
        ]

    @contextlib.contextmanager
    def _create_session_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
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

        session_info = session_infos[0]
        with closing_session(session_constructor(session_info)) as session:
            with self._cache_session(session_info.session_name, session):
                new_session_info = session_info._with_session(session)
                yield cast(TypedSessionInformation[TSession], new_session_info)

    @contextlib.contextmanager
    def _create_sessions_core(
        self,
        session_constructor: Callable[[SessionInformation], TSession],
        instrument_type_id: str,
    ) -> Generator[Sequence[TypedSessionInformation[TSession]], None, None]:
        if not instrument_type_id:
            raise ValueError("This method requires an instrument type ID.")
        session_infos = self._get_matching_session_infos(instrument_type_id)
        if len(session_infos) == 0:
            raise ValueError(
                f"No reserved sessions matched instrument type ID '{instrument_type_id}'. "
                "Expected single or multiple sessions, got 0 sessions."
            )

        with ExitStack() as stack:
            typed_session_infos: List[TypedSessionInformation[TSession]] = []
            for session_info in session_infos:
                session = stack.enter_context(closing_session(session_constructor(session_info)))
                stack.enter_context(self._cache_session(session_info.session_name, session))
                new_session_info = session_info._with_session(session)
                typed_session_infos.append(
                    cast(TypedSessionInformation[TSession], new_session_info)
                )
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
            session_constructor: A function that constructs sessions based on
                session information.

            instrument_type_id: Instrument type ID for the session.

                For custom instruments, use the instrument type id defined in
                the pin map file.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

        Raises:
            ValueError: If the instrument type ID is empty, no reserved sessions
                match the instrument type ID, or too many reserved sessions
                match the instrument type ID.
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
            session_constructor: A function that constructs sessions based on
                session information.

            instrument_type_id: Instrument type ID for the session.

                For custom instruments, use the instrument type id defined in
                the pin map file.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
            field.

        Raises:
            ValueError: If the instrument type ID is empty or no reserved
                sessions match the instrument type ID.
        """
        return self._create_sessions_core(session_constructor, instrument_type_id)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidaqmx_task(
        self,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidaqmx.Task]]:
        """Create a single NI-DAQmx task.

        Args:
            initialization_behavior: Specifies whether to initialize a new
                task or attach to an existing task.

        Returns:
            A context manager that yields a session information object. The
            created task is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_DAQMX)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidaqmx_tasks(
        self,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidcpower.Session]]]:
        """Create multiple NI-DAQmx tasks.

        Args:
            initialization_behavior: Specifies whether to initialize a new
                task or attach to an existing task.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created tasks are available via the ``session``
            field.

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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_DAQMX)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidcpower_session(
        self,
        reset: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidcpower.Session]]:
        """Create a single NI-DCPower instrument session.

        Args:
            reset: Specifies whether to reset channel(s) during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDCPOWER_SIMULATE``, ``NIDCPOWER_BOARD_TYPE``, and
                ``NIDCPOWER_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_DCPOWER)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidcpower_sessions(
        self,
        reset: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidcpower.Session]]]:
        """Create multiple NI-DCPower instrument sessions.

        Args:
            reset: Specifies whether to reset channel(s) during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDCPOWER_SIMULATE``, ``NIDCPOWER_BOARD_TYPE``, and
                ``NIDCPOWER_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_DCPOWER)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidigital_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidigital.Session]]:
        """Create a single NI-Digital Pattern instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDIGITAL_SIMULATE``, ``NIDIGITAL_BOARD_TYPE``, and
                ``NIDIGITAL_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidigital_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidigital.Session]]]:
        """Create multiple NI-Digital Pattern instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDIGITAL_SIMULATE``, ``NIDIGITAL_BOARD_TYPE``, and
                ``NIDIGITAL_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidmm_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nidmm.Session]]:
        """Create a single NI-DMM instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDMM_SIMULATE``, ``NIDMM_BOARD_TYPE``, and
                ``NIDMM_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_DMM)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nidmm_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nidmm.Session]]]:
        """Create multiple NI-DMM instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIDMM_SIMULATE``, ``NIDMM_BOARD_TYPE``, and
                ``NIDMM_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_DMM)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nifgen_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[nifgen.Session]]:
        """Create a single NI-FGEN instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIFGEN_SIMULATE``, ``NIFGEN_BOARD_TYPE``, and ``NIFGEN_MODEL``
                in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_FGEN)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_nifgen_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[nifgen.Session]]]:
        """Create multiple NI-FGEN instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NIFGEN_SIMULATE``, ``NIFGEN_BOARD_TYPE``, and ``NIFGEN_MODEL``
                in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_FGEN)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_niscope_session(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[niscope.Session]]:
        """Create a single NI-SCOPE instrument session.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NISCOPE_SIMULATE``, ``NISCOPE_BOARD_TYPE``, and
                ``NISCOPE_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_SCOPE)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_niscope_sessions(
        self,
        reset_device: bool = False,
        options: Optional[Dict[str, Any]] = None,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[niscope.Session]]]:
        """Create multiple NI-SCOPE instrument sessions.

        Args:
            reset_device: Specifies whether to reset the instrument during the
                initialization procedure.

            options: Specifies the initial value of certain properties for the
                session. If this argument is not specified, the default value is
                an empty dict, which you may override by specifying
                ``NISCOPE_SIMULATE``, ``NISCOPE_BOARD_TYPE``, and
                ``NISCOPE_MODEL`` in the configuration file (``.env``).

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_SCOPE)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_niswitch_session(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[TypedSessionInformation[niswitch.Session]]:
        """Create a single NI-SWITCH relay driver instrument session.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``NISWITCH_TOPOLOGY`` in the
                configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting ``NISWITCH_SIMULATE`` in the
                configuration file (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a session information object. The
            created session is available via the ``session`` field.

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
        return self._create_session_core(session_constructor, INSTRUMENT_TYPE_NI_RELAY_DRIVER)

    @requires_feature(SESSION_MANAGEMENT_2024Q1)
    def create_niswitch_sessions(
        self,
        topology: Optional[str] = None,
        simulate: Optional[bool] = None,
        reset_device: bool = False,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> ContextManager[Sequence[TypedSessionInformation[niswitch.Session]]]:
        """Create multiple NI-SWITCH relay driver instrument sessions.

        Args:
            topology: Specifies the switch topology. If this argument is not
                specified, the default value is "Configured Topology", which you
                may override by setting ``NISWITCH_TOPOLOGY`` in the
                configuration file (``.env``).

            simulate: Enables or disables simulation of the switch module. If
                this argument is not specified, the default value is ``False``,
                which you may override by setting ``NISWITCH_SIMULATE`` in the
                configuration file (``.env``).

            reset_device: Specifies whether to reset the switch module during
                the initialization procedure.

            initialization_behavior: Specifies whether to initialize a new
                session or attach to an existing session.

        Returns:
            A context manager that yields a sequence of session information
            objects. The created sessions are available via the ``session``
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
        return self._create_sessions_core(session_constructor, INSTRUMENT_TYPE_NI_RELAY_DRIVER)


class SingleSessionReservation(BaseReservation):
    """Manages reservation for a single session."""

    @property
    def session_info(self) -> SessionInformation:
        """Single session information object."""
        assert len(self._session_info) == 1
        return self._session_info[0]


class MultiSessionReservation(BaseReservation):
    """Manages reservation for multiple sessions."""

    @property
    def session_info(self) -> List[SessionInformation]:
        """Multiple session information objects."""
        return self._session_info

"""Types and submodules for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
from typing import (
    ContextManager,
    Generic,
    Protocol,
    Type,
    TypeVar,
    cast,
    runtime_checkable,
)

import grpc

TSessionInitializationBehavior = TypeVar("TSessionInitializationBehavior", bound=int)
TSessionInitializationBehavior_co = TypeVar(
    "TSessionInitializationBehavior_co", bound=int, covariant=True
)


class SessionInitializationBehaviorEnumType(Protocol, Generic[TSessionInitializationBehavior_co]):
    """Protocol describing a driver API's SessionInitializationBehavior IntEnum type.

    Each driver API has its own version of this IntEnum, which provides the same
    enum values.
    """

    # This protocol describes the provided enum values and nothing else.
    #
    # Python 3.11 doesn't have a good way to describe read-only class variables
    # or protocols that inherit from built-in types such as int.

    @property
    def AUTO(  # noqa: N802 - function name should be lowercase
        self,
    ) -> TSessionInitializationBehavior_co:
        """Automatically initialize a new session or attach to an existing one."""
        ...

    @property
    def INITIALIZE_SERVER_SESSION(  # noqa: N802 - function name should be lowercase
        self,
    ) -> TSessionInitializationBehavior_co:
        """Always initialize a new session."""
        ...

    @property
    def ATTACH_TO_SERVER_SESSION(  # noqa: N802 - function name should be lowercase
        self,
    ) -> TSessionInitializationBehavior_co:
        """Always attach to an existing session."""
        ...


class GrpcSessionOptions(Protocol, Generic[TSessionInitializationBehavior]):
    """Protocol describing a driver API's GrpcSessionOptions class.

    Each driver API has its own version of this class, which implicitly
    implements this protocol.
    """

    def __init__(
        self,
        grpc_channel: grpc.Channel,
        session_name: str,
        *,
        initialization_behavior: TSessionInitializationBehavior = cast(
            TSessionInitializationBehavior, 0
        ),
    ) -> None:
        """Construct a GrpcSessionOptions."""
        ...

    grpc_channel: grpc.Channel
    session_name: str
    initialization_behavior: TSessionInitializationBehavior


@runtime_checkable
class DriverModule(Protocol, Generic[TSessionInitializationBehavior]):
    """Protocol describing a driver API module.

    Supported driver APIs (nimi-python and nidaqmx-python) implicitly implement
    this protocol.
    """

    @property
    def GRPC_SERVICE_INTERFACE_NAME(self) -> str:  # noqa: N802 - function name should be lowercase
        """The gRPC interface name for NI gRPC Device Server for this API."""
        ...

    @property
    def SessionInitializationBehavior(  # noqa: N802 - function name should be lowercase
        self,
    ) -> SessionInitializationBehaviorEnumType[TSessionInitializationBehavior]:
        """The SessionInitializationBehavior enum type for this API."""
        ...

    @property
    def GrpcSessionOptions(  # noqa: N802 - function name should be lowercase
        self,
    ) -> Type[GrpcSessionOptions[TSessionInitializationBehavior]]:
        """The GrpcSessionOptions class for this API."""
        ...


TSession = TypeVar("TSession")


def closing_session(session: TSession) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Args:
        session: A driver session.

    Returns:
        A context manager that yields the session and closes it.
    """
    if isinstance(session, contextlib.AbstractContextManager):
        # Assume the session yields itself.
        return session
    elif hasattr(session, "close"):
        return contextlib.closing(session)
    else:
        raise TypeError(
            f"Invalid session type '{type(session)}'. A session must be a context manager and/or "
            "have a close() method."
        )

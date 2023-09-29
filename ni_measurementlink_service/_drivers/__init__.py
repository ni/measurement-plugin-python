"""Types and submodules for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
from typing import (
    ClassVar,
    ContextManager,
    Generic,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

import grpc


class SessionInitializationBehavior(Protocol):
    """IntEnum specifying whether to initialize a new session or attach to an existing one.

    Each driver API has its own version of this enum.
    """

    AUTO: ClassVar[int]
    INITIALIZE_SERVER_SESSION: ClassVar[int]
    ATTACH_TO_SERVER_SESSION: ClassVar[int]

    name: str
    value: int


TSessionInitializationBehavior = TypeVar(
    "TSessionInitializationBehavior", bound=SessionInitializationBehavior
)


class GrpcSessionOptions(Protocol, Generic[TSessionInitializationBehavior]):
    """gRPC options for driver sessions.

    Each driver API has its own version of this class.
    """

    grpc_channel: grpc.Channel
    session_name: str
    initialization_behavior: TSessionInitializationBehavior


@runtime_checkable
class DriverModule(Protocol, Generic[TSessionInitializationBehavior]):
    """A driver API module."""

    @property
    def GRPC_SERVICE_INTERFACE_NAME(self) -> str:  # noqa: N802 - function name should be lowercase
        """The gRPC interface name for NI gRPC Device Server for this API."""
        ...

    @property
    def SessionInitializationBehavior(  # noqa: N802 - function name should be lowercase
        self,
    ) -> Type[TSessionInitializationBehavior]:
        """The SessionInitializationBehavior enum for this API."""
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

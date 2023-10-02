"""Types and submodules for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
import sys
from typing import (
    TYPE_CHECKING,
    ClassVar,
    ContextManager,
    Generic,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

import grpc

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class SessionInitializationBehavior(Protocol):
    """Protocol describing a driver API's SessionInitializationBehavior IntEnum.

    Each driver API has its own version of this enum, which implicitly
    implements this protocol.
    """

    AUTO: ClassVar[Self]
    INITIALIZE_SERVER_SESSION: ClassVar[Self]
    ATTACH_TO_SERVER_SESSION: ClassVar[Self]

    name: str
    value: int


TSessionInitializationBehavior = TypeVar(
    "TSessionInitializationBehavior", bound=SessionInitializationBehavior
)


class GrpcSessionOptions(Protocol, Generic[TSessionInitializationBehavior]):
    """Protocol describing a driver API's GrpcSessionOptions class.

    Each driver API has its own version of this class, which implicitly
    implements this protocol.
    """

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

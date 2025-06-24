"""Fake driver API for testing."""

from __future__ import annotations

import sys
from enum import Enum, IntEnum
from types import TracebackType
from typing import TYPE_CHECKING, Any, ContextManager

if TYPE_CHECKING:
    import grpc

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


GRPC_SERVICE_INTERFACE_NAME = "nifake_grpc.NiFake"

# The GrpcSessionOptions classes in nimi-python and nidaqmx-python have an api_key field.
_API_KEY = "00000000-0000-0000-0000-000000000000"


class SessionInitializationBehavior(IntEnum):
    """Specifies whether to initialize a new session or attach to an existing session."""

    AUTO = 0
    INITIALIZE_SERVER_SESSION = 1
    ATTACH_TO_SERVER_SESSION = 2
    INITIALIZE_SESSION_THEN_DETACH = 3
    ATTACH_TO_SESSION_THEN_CLOSE = 4


_CLOSE_BEHAVIORS = [
    SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE,
]


class GrpcSessionOptions:
    """gRPC session options."""

    def __init__(
        self,
        grpc_channel: grpc.Channel,
        session_name: str,
        *,
        api_key: str = _API_KEY,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> None:
        """Initialize the gRPC session options."""
        self.grpc_channel = grpc_channel
        self.session_name = session_name
        self.api_key = api_key
        self.initialization_behavior = initialization_behavior


class MeasurementType(Enum):
    """Measurement type."""

    VOLTAGE = 1
    CURRENT = 2


class _Acquisition:
    def __init__(self, session: _SessionBase) -> None:
        self._session = session

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.abort()


class _SessionBase:
    """Base class for driver sessions."""

    def __init__(
        self,
        resource_name: str,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        options: dict[str, Any] = {},
    ) -> None:
        """Initialize the session."""
        self.resource_name = resource_name
        self.initialization_behavior = initialization_behavior
        self.options = options
        self.is_closed = False

    def configure(self, measurement_type: MeasurementType, range: float) -> None:
        """Configure the session."""
        pass

    def initiate(self) -> ContextManager[object]:
        """Initiate an acquisition."""
        return _Acquisition(self)

    def abort(self) -> None:
        """Abort (stop) the acquisition."""
        pass

    def read(self) -> float:
        """Read a sample."""
        return 0.0


class ClosableSession(_SessionBase):
    """A driver session that supports close()."""

    def close(self) -> None:
        """Close the session."""
        self.is_closed = True


class ContextManagerSession(_SessionBase):
    """A driver session that supports the context manager protocol."""

    def __enter__(self) -> Self:
        """Enter the session's runtime context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the session's runtime context."""
        self.is_closed = True


class Session(_SessionBase):
    """A driver session that supports both close() and the context manager protocol."""

    def __init__(
        self,
        resource_name: str,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
        options: dict[str, Any] = {},
    ) -> None:
        """Initialize the session."""
        self.resource_name = resource_name
        self.initialization_behavior = initialization_behavior
        self.options = options
        self.is_closed = False

    def close(self) -> None:
        """Close the session."""
        self.is_closed = True

    def __enter__(self) -> Self:
        """Enter the session's runtime context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the session's runtime context."""
        if self.initialization_behavior in _CLOSE_BEHAVIORS:
            self.close()

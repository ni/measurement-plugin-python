"""Fake driver API for testing."""
from __future__ import annotations

import sys
from enum import Enum
from types import TracebackType
from typing import TYPE_CHECKING, Any, ContextManager, Dict, Optional, Type

from ni_measurementlink_service.session_management._types import SessionInitializationBehavior

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


GRPC_SERVICE_INTERFACE_NAME = "nifake_grpc.NiFake"

_CLOSE_BEHAVIORS = [
    SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE,
]


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
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._session.abort()


class _SessionBase:
    """Base class for driver sessions."""

    def __init__(self, resource_name: str, options: Dict[str, Any] = {}) -> None:
        """Initialize the session."""
        self.resource_name = resource_name
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
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the session's runtime context."""
        self.is_closed = True


class Session(_SessionBase):
    """A driver session that supports both close() and the context manager protocol."""

    def __init__(self, resource_name: str, options: Dict[str, Any] = {}) -> None:
        """Initialize the session."""
        self.resource_name = resource_name
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
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the session's runtime context."""
        if (
            "initialization_behavior" not in self.options
            or self.options["initialization_behavior"] in _CLOSE_BEHAVIORS
        ):
            self.close()

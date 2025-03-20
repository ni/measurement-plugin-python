"""Fake driver API for testing."""

from __future__ import annotations

import sys
from enum import Enum, IntEnum
from types import TracebackType
from typing import TYPE_CHECKING

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


class RelayAction(Enum):
    """Relay action."""

    OPEN = 1
    CLOSE = 2


class _MultiplexerSessionBase:
    """Base class for multiplexer driver sessions."""

    def __init__(
        self,
        resource_name: str,
        topology: str | None = None,
        reset_device: bool = True,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> None:
        """Initialize the multiplexer session."""
        self.resource_name = resource_name
        self.topology = topology
        self.reset_device = reset_device
        self.initialization_behavior = initialization_behavior
        self.is_closed = False

    def relay_control(self, relay_name: str, relay_action: RelayAction) -> None:
        """Controls individual relays of the switch."""
        pass

    def connect_multiple(self, connection_list: str) -> None:
        """Creates the connections between channels specified in connection list."""
        pass

    def disconnect_multiple(self, connection_list: str) -> None:
        """Breaks the connections between channels specified in disconnection list."""
        pass

    def wait_for_debounce(self) -> None:
        """Pauses until all created paths have settled."""
        pass

    def abort(self) -> None:
        """Abort (stop) the acquisition."""
        pass


class ClosableSession(_MultiplexerSessionBase):
    """A driver session that supports close()."""

    def close(self) -> None:
        """Close the session."""
        self.is_closed = True


class ContextManagerSession(_MultiplexerSessionBase):
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


class Session(_MultiplexerSessionBase):
    """A multiplexer driver session that supports both close() and the context manager protocol."""

    def __init__(
        self,
        resource_name: str,
        topology: str | None = None,
        reset_device: bool = True,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> None:
        """Initialize the multiplexer session."""
        self.resource_name = resource_name
        self.topology = topology
        self.reset_device = reset_device
        self.initialization_behavior = initialization_behavior
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

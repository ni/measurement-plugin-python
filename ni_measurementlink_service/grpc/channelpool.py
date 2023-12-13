"""gRPC channel pool."""

from __future__ import annotations

import sys
from threading import Lock
from types import TracebackType
from typing import (
    Dict,
    Literal,
    Optional,
    Type,
    TYPE_CHECKING,
)

import grpc

from ni_measurementlink_service.grpc.loggers import ClientLogger

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class GrpcChannelPool(object):
    """Class that manages gRPC channel lifetimes."""

    def __init__(self) -> None:
        """Initialize the GrpcChannelPool object."""
        self._lock: Lock = Lock()
        self._channel_cache: Dict[str, grpc.Channel] = {}

    def __enter__(self: Self) -> Self:
        """Enter the runtime context of the GrpcChannelPool."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        """Exit the runtime context of the GrpcChannelPool."""
        self.close()
        return False

    def get_channel(self, target: str) -> grpc.Channel:
        """Return a gRPC channel.

        Args:
            target (str): The server address

        """
        new_channel = None
        with self._lock:
            if target not in self._channel_cache:
                self._lock.release()
                new_channel = grpc.insecure_channel(target)
                if ClientLogger.is_enabled():
                    new_channel = grpc.intercept_channel(new_channel, ClientLogger())
                self._lock.acquire()
                if target not in self._channel_cache:
                    self._channel_cache[target] = new_channel
                    new_channel = None
            channel = self._channel_cache[target]

        # Close new_channel if it was not stored in _channel_cache.
        if new_channel is not None:
            new_channel.close()

        return channel

    def close(self) -> None:
        """Close channels opened by get_channel()."""
        with self._lock:
            for channel in self._channel_cache.values():
                channel.close()
            self._channel_cache.clear()

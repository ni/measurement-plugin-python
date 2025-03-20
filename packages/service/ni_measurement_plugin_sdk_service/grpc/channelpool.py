"""gRPC channel pool."""

from __future__ import annotations

import ipaddress
import re
import sys
from threading import Lock
from types import TracebackType
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlparse

import grpc

from ni_measurement_plugin_sdk_service.grpc.loggers import ClientLogger

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class GrpcChannelPool:
    """Class that manages gRPC channel lifetimes."""

    def __init__(self) -> None:
        """Initialize the GrpcChannelPool object."""
        self._lock: Lock = Lock()
        self._channel_cache: dict[str, grpc.Channel] = {}

    def __enter__(self: Self) -> Self:
        """Enter the runtime context of the GrpcChannelPool."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
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
                new_channel = self._create_channel(target)
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

    def _create_channel(self, target: str) -> grpc.Channel:
        options = [
            ("grpc.max_receive_message_length", -1),
            ("grpc.max_send_message_length", -1),
        ]
        if self._is_local(target):
            options.append(("grpc.enable_http_proxy", 0))
        channel = grpc.insecure_channel(target, options)
        if ClientLogger.is_enabled():
            channel = grpc.intercept_channel(channel, ClientLogger())
        return channel

    def _is_local(self, target: str) -> bool:
        hostname = ""
        # First, check if the target string is in URL format
        parse_result = urlparse(target)
        if parse_result.scheme and parse_result.hostname and parse_result.port:
            hostname = parse_result.hostname
        else:
            # Next, check for target string in <host_name>:<port> format
            match = re.match(r"^(.*):(\d+)$", target)
            if match:
                hostname = match.group(1)

        if not hostname:
            return False
        if hostname == "localhost" or hostname == "LOCALHOST":
            return True

        # IPv6 addresses don't support parsing with leading/trailing brackets
        # so we need to remove them.
        match = re.match(r"^\[(.*)\]$", hostname)
        if match:
            hostname = match.group(1)

        try:
            address = ipaddress.ip_address(hostname)
            return address.is_loopback
        except ValueError:
            return False

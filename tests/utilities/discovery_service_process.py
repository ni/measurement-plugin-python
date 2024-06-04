"""Class to create and terminate Discovery Service instance."""

from types import TracebackType
from typing import Optional, Type

from typing_extensions import Self

from ni_measurement_plugin_sdk.discovery._support import (
    _get_discovery_service_location,
    _get_key_file_path,
    _service_already_running,
    _start_service,
)


class DiscoveryServiceProcess:
    """Maintains the processes involved in creating and terminating discovery service."""

    def __init__(self) -> None:
        """Creates a DiscoveryServiceProcess instance."""
        try:
            self._proc = None
            key_file_path = _get_key_file_path()
            if _service_already_running(key_file_path):
                return
            self._proc = _start_service(_get_discovery_service_location(), key_file_path)
        except Exception:
            self._close_discovery_service()
            raise

    def __enter__(self: Self) -> Self:
        """Returns the DiscoveryServiceProcess instance."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Closes the DiscoveryServiceProcess instance."""
        self._close_discovery_service()

    def _close_discovery_service(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            # Use communicate() to close the stdout pipe and wait for the server process to exit.
            self._proc.communicate()

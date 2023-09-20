"""Client for accessing the MeasurementLink discovery service."""
import json
import logging
import os
import pathlib
import subprocess
import sys
import threading
import time
import typing
from typing import Any, Dict, Optional

import grpc
from deprecation import deprecated

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
    discovery_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.info import MeasurementInfo, ServiceInfo

if sys.platform == "win32":
    import errno
    import msvcrt

    import win32con
    import win32file
    import winerror

_logger = logging.getLogger(__name__)
# Save Popen object to avoid "ResourceWarning: subprocess N is still running"
_discovery_service_subprocess: Optional[subprocess.Popen] = None

_START_SERVICE_TIMEOUT = 30.0
_START_SERVICE_POLLING_INTERVAL = 100e-3


class ServiceLocation(typing.NamedTuple):
    """Represents the location of a service."""

    location: str
    insecure_port: str
    ssl_authenticated_port: str

    @property
    def insecure_address(self) -> str:
        """Get the service's insecure address in the format host:port."""
        return f"{self.location}:{self.insecure_port}"

    @property
    def ssl_authenticated_address(self) -> str:
        """Get the service's SSL-authenticated address in the format host:port."""
        return f"{self.location}:{self.ssl_authenticated_port}"


class DiscoveryClient:
    """Client for accessing the MeasurementLink discovery service."""

    def __init__(
        self,
        stub: Optional[discovery_service_pb2_grpc.DiscoveryServiceStub] = None,
        *,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ) -> None:
        """Initialize the discovery client.

        Args:
            stub: An optional discovery service gRPC stub for unit testing.

            grpc_channel_pool: An optional gRPC channel pool (recommended).
        """
        self._initialization_lock = threading.Lock()
        self._grpc_channel_pool = grpc_channel_pool or GrpcChannelPool()
        self._stub = stub
        self._registration_id = ""

    @property
    @deprecated(
        deprecated_in="1.2.0-dev2",
        details="This property should not be public and will be removed in a later release.",
    )
    def registration_id(self) -> str:
        """ "The ID from discovery service upon successful registration."""
        return self._registration_id

    @property
    @deprecated(
        deprecated_in="1.2.0-dev2",
        details="This property should not be public and will be removed in a later release.",
    )
    def stub(self) -> discovery_service_pb2_grpc.DiscoveryServiceStub:
        """Get the gRPC stub used to interact with the discovery service."""
        return self._get_stub()

    def _get_stub(self) -> discovery_service_pb2_grpc.DiscoveryServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._stub is None:
                    address = _get_discovery_service_address()
                    channel = self._grpc_channel_pool.get_channel(address)
                    self._stub = discovery_service_pb2_grpc.DiscoveryServiceStub(channel)
        return self._stub

    @deprecated(deprecated_in="1.2.0-dev2", details="Use register_service instead.")
    def register_measurement_service(
        self, service_port: str, service_info: ServiceInfo, measurement_info: MeasurementInfo
    ) -> bool:
        """Register the measurement service with the discovery service.

        Args:
            service_port: The port number of the service.

            service_info: Information describing the service.

            measurement_info: Information describing the measurement.

        Returns:
            Boolean indicating whether the service was successfully registered.
        """
        if self._registration_id:
            raise RuntimeError("Service already registered")

        service_location = ServiceLocation(
            location="localhost",
            insecure_port=service_port,
            ssl_authenticated_port="",
        )

        self._registration_id = self.register_service(
            service_info._replace(display_name=measurement_info.display_name),
            service_location,
        )
        return True

    def register_service(self, service_info: ServiceInfo, service_location: ServiceLocation) -> str:
        """Register the specified service with the discovery service.

        Args:
            service_info: Information describing the service.

            service_location: The location of the service on the network.

        Returns:
            ID that can be used to unregister the service.
        """
        try:
            grpc_service_description = discovery_service_pb2.ServiceDescriptor(
                display_name=service_info.display_name,
                description_url=service_info.description_url,
                provided_interfaces=service_info.provided_interfaces,
                service_class=service_info.service_class,
                annotations=service_info.annotations,
            )

            grpc_service_location = discovery_service_pb2.ServiceLocation(
                location=service_location.location,
                insecure_port=service_location.insecure_port,
                ssl_authenticated_port=service_location.ssl_authenticated_port,
            )

            request = discovery_service_pb2.RegisterServiceRequest(
                service_description=grpc_service_description,
                location=grpc_service_location,
            )

            response = self._get_stub().RegisterService(request)
            _logger.info("Successfully registered with discovery service.")
            return response.registration_id
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to register with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in registering with discovery service.")
            raise
        except FileNotFoundError:
            _logger.error(
                "Unable to register with discovery service. Possible reason: discovery service not running."
            )
            raise
        except Exception:
            _logger.exception("Error in registering with discovery service.")
            raise

    def unregister_service(self, registration_id: str = "") -> bool:
        """Unregisters the specified service from the discovery service.

        This method should be called before the service exits.

        Args:
            registration_id: The registration ID returned from register_service.
                This argument should be omitted after calling the deprecated
                register_measurement_service method.

        Returns:
            Boolean indicating whether the service was unregistered.
        """
        try:
            if not registration_id:
                registration_id = self._registration_id
                if not registration_id:
                    _logger.info("Not registered with discovery service.")
                    return False

            request = discovery_service_pb2.UnregisterServiceRequest(
                registration_id=registration_id
            )

            _ = self._get_stub().UnregisterService(request)
            _logger.info("Successfully unregistered with discovery service.")

            if registration_id == self._registration_id:
                self._registration_id = ""

            return True
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to unregister with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in unregistering with discovery service.")
            raise
        except FileNotFoundError:
            _logger.error(
                "Unable to unregister with discovery service. Possible reason: discovery service not running."
            )
            raise
        except Exception:
            _logger.exception("Error in unregistering with discovery service.")
            raise

    def resolve_service(self, provided_interface: str, service_class: str = "") -> ServiceLocation:
        """Resolve the location of a service.

        Given a description of a service, returns information that can be used to establish
        communication with that service. If necessary, the service will be started by the
        discovery service if it has not already been started.

        Args:
            provided_interface: The gRPC full name of the service.
            service_class: The service "class" that should be matched. If the value is not
                specified and there is more than one matching service registered, an error
                is returned.

        Returns:
            The service location.
        """
        request = discovery_service_pb2.ResolveServiceRequest(
            provided_interface=provided_interface, service_class=service_class
        )

        response = self._get_stub().ResolveService(request)

        return ServiceLocation(
            location=response.location,
            insecure_port=response.insecure_port,
            ssl_authenticated_port=response.ssl_authenticated_port,
        )


def _get_discovery_service_address() -> str:
    key_file_path = _get_key_file_path()
    _ensure_discovery_service_started(key_file_path)
    _logger.debug("Discovery service key file path: %s", key_file_path)
    with _open_key_file(str(key_file_path)) as key_file:
        key_json = json.load(key_file)
        return "localhost:" + key_json["InsecurePort"]


def _ensure_discovery_service_started(key_file_path: pathlib.Path) -> None:
    """Check whether discovery service already running, if not start the discovery service."""
    if _service_already_running(key_file_path):
        return

    exe_file_path = _get_discovery_service_location()
    global _discovery_service_subprocess  # save Popen object to avoid ResourceWarning
    _discovery_service_subprocess = _start_service(exe_file_path, key_file_path)


def _get_discovery_service_location() -> pathlib.PurePath:
    """Gets the location of the discovery service process executable."""
    registration_json_path = _get_registration_json_file_path()
    registration_json_obj = json.loads(registration_json_path.read_text())
    return registration_json_path.parent / registration_json_obj["discovery"]["path"]


def _get_registration_json_file_path() -> pathlib.Path:
    if sys.platform == "win32":
        return (
            pathlib.Path(os.environ["ProgramW6432"])
            / "National Instruments"
            / "Shared"
            / "MeasurementLink"
            / "MeasurementLinkServices.json"
        )
    else:
        raise NotImplementedError("Platform not supported")


def _key_file_exists(key_file_path: pathlib.Path) -> bool:
    return key_file_path.is_file() and key_file_path.stat().st_size > 0


def _start_service(
    exe_file_path: pathlib.PurePath, key_file_path: pathlib.Path
) -> subprocess.Popen:
    """Starts the service at the specified path and wait for the service to get up and running."""
    kwargs: Dict[str, Any] = {}
    if sys.platform == "win32":
        # Terminating the measurement service should not terminate the discovery service.
        kwargs["creationflags"] = subprocess.CREATE_BREAKAWAY_FROM_JOB
    discovery_service_subprocess = subprocess.Popen(
        [exe_file_path],
        cwd=exe_file_path.parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    # After the execution of process, check for key file existence in the path
    # stop checking after 30 seconds have elapsed and throw error
    timeout_time = time.time() + _START_SERVICE_TIMEOUT
    while True:
        try:
            with _open_key_file(str(key_file_path)) as _:
                return discovery_service_subprocess
        except IOError:
            pass
        if time.time() >= timeout_time:
            raise TimeoutError("Timed out waiting for discovery service to start")
        time.sleep(_START_SERVICE_POLLING_INTERVAL)


def _service_already_running(key_file_path: pathlib.Path) -> bool:
    try:
        _delete_existing_key_file(key_file_path)
    except IOError:
        return True
    return False


def _delete_existing_key_file(key_file_path: pathlib.Path) -> None:
    if _key_file_exists(key_file_path):
        with key_file_path.open("w") as _:
            pass
        key_file_path.unlink()


def _get_key_file_path(cluster_id: Optional[str] = None) -> pathlib.Path:
    if cluster_id is not None:
        return _get_key_file_directory() / f"DiscoveryService_{cluster_id}.json"
    return _get_key_file_directory() / "DiscoveryService.json"


def _get_key_file_directory() -> pathlib.Path:
    version = discovery_service_pb2.DESCRIPTOR.package.split(".")[-1]
    if sys.platform == "win32":
        return (
            pathlib.Path(os.environ["ProgramData"])
            / "National Instruments"
            / "MeasurementLink"
            / "Discovery"
            / version
        )
    else:
        raise NotImplementedError("Platform not supported")


def _open_key_file(path: str) -> typing.TextIO:
    if sys.platform == "win32":
        # Use the Win32 API to specify the share mode. Otherwise, opening the file throws
        # PermissionError due to a sharing violation. This is a workaround for
        # https://github.com/python/cpython/issues/59449
        # (Support for opening files with FILE_SHARE_DELETE on Windows).
        try:
            win32_file_handle = win32file.CreateFile(
                path,
                win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ
                | win32file.FILE_SHARE_WRITE
                | win32file.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                0,
                None,
            )
        except win32file.error as e:
            if e.winerror == winerror.ERROR_FILE_NOT_FOUND:
                raise FileNotFoundError(errno.ENOENT, e.strerror, path) from e
            elif (
                e.winerror == winerror.ERROR_ACCESS_DENIED
                or e.winerror == winerror.ERROR_SHARING_VIOLATION
            ):
                raise PermissionError(errno.EACCES, e.strerror, path) from e
            raise

        # The CRT file descriptor takes ownership of the Win32 file handle.
        # os.O_TEXT is unnecessary because Python handles newline conversion.
        crt_file_descriptor = msvcrt.open_osfhandle(win32_file_handle.handle, os.O_RDONLY)
        win32_file_handle.Detach()

        # The Python file object takes ownership of the CRT file descriptor. Closing the Python
        # file object closes the underlying Win32 file handle.
        return os.fdopen(crt_file_descriptor, "r", encoding="utf-8-sig")
    else:
        return open(path, "r")

""" Contains API to register and un-register measurement service with discovery service.
"""
import json
import logging
import os
import pathlib
import sys
import typing

import grpc

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


_PROVIDED_MEASUREMENT_SERVICE = "ni.measurementlink.measurement.v1.MeasurementService"

_logger = logging.getLogger(__name__)


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
    """Class that contains APIs need to interact with discovery service.

    Attributes
    ----------
        stub (DiscoveryServiceStub): The gRPC stub used to interact with the discovery
        service.

        registration_id(string): The ID from discovery service upon successful registration.

    """

    def __init__(self, stub: discovery_service_pb2_grpc.DiscoveryServiceStub = None):
        """Initialize the Discovery Client with provided registry service stub.

        Args:
            stub (DiscoveryServiceStub, optional): The gRPC stub to interact with discovery
            service. Defaults to None.

        """
        self._stub = stub
        self.registration_id = ""

    @property
    def stub(self) -> discovery_service_pb2_grpc.DiscoveryServiceStub:
        """Get the gRPC stub used to interact with the discovery service."""
        if self._stub is None:
            address = _get_discovery_service_address()
            channel = grpc.insecure_channel(address)
            self._stub = discovery_service_pb2_grpc.DiscoveryServiceStub(channel)
        return self._stub

    def register_measurement_service(
        self, service_port: str, service_info: ServiceInfo, measurement_info: MeasurementInfo
    ) -> bool:
        """Register the measurement service with the discovery service.

        Args:
        ----
            service_port (str): Port Number of the measurement service.

            service_info (ServiceInfo): Service Info.

            display_name (str): Display name of the service.

        Returns
        -------
            bool: Boolean to represent if the registration is successful.

        """
        try:
            # Service Location
            service_location = discovery_service_pb2.ServiceLocation()
            service_location.location = "localhost"
            service_location.insecure_port = service_port
            # Service Descriptor
            service_descriptor = discovery_service_pb2.ServiceDescriptor()
            service_descriptor.display_name = measurement_info.display_name
            service_descriptor.service_class = service_info.service_class
            service_descriptor.description_url = service_info.description_url
            service_descriptor.provided_interfaces.append(_PROVIDED_MEASUREMENT_SERVICE)

            # Registration Request Creation
            request = discovery_service_pb2.RegisterServiceRequest(
                location=service_location, service_description=service_descriptor
            )
            # Registration RPC Call
            register_response = self.stub.RegisterService(request)
            self.registration_id = register_response.registration_id
            _logger.info("Successfully registered with discovery service.")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to register with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in registering with discovery service.")
            return False
        except FileNotFoundError:
            _logger.error(
                "Unable to register with discovery service. Possible reason: discovery service not running."
            )
        except Exception:
            _logger.exception("Error in registering with discovery service.")
            return False
        return True

    def unregister_service(self) -> bool:
        """Un-registers the measurement service from the discovery service.

        Should be called before the service is closed.

        Returns
        -------
            bool: Boolean to represent if the un-registration is successful.

        """
        try:
            if self.registration_id:
                # Un-registration Request Creation
                request = discovery_service_pb2.UnregisterServiceRequest(
                    registration_id=self.registration_id
                )
                # Un-registration RPC Call
                self.stub.UnregisterService(request)
                _logger.info("Successfully unregistered with discovery service.")
            else:
                _logger.info("Not registered with discovery service.")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to unregister with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in unregistering with discovery service.")
            return False
        except FileNotFoundError:
            _logger.error(
                "Unable to unregister with discovery service. Possible reason: discovery service not running."
            )
        except Exception:
            _logger.exception("Error in unregistering with discovery service.")
            return False
        return True

    def resolve_service(self, provided_interface: str, service_class: str = "") -> ServiceLocation:
        """Resolve the location of a service.

        Given a description of a service, returns information that can be used to establish
        communication with that service. If necessary, the service will be started by the
        discovery service if it has not already been started.

        Args:
        ----
            provided_interface: The gRPC Full Name of the service.
            service_class: The service "class" that should be matched. If the value is not
                specified and there is more than one matching service registered, an error
                is returned.

        Returns
        -------
            A ServiceLocation location object that represents the location of a service.

        """
        request = discovery_service_pb2.ResolveServiceRequest()
        request.provided_interface = provided_interface
        request.service_class = service_class

        response: discovery_service_pb2.ServiceLocation = self.stub.ResolveService(request)

        return ServiceLocation(
            location=response.location,
            insecure_port=response.insecure_port,
            ssl_authenticated_port=response.ssl_authenticated_port,
        )


def _get_discovery_service_address() -> str:
    key_file_path = _get_key_file_path()
    _logger.debug("Discovery service key file path: %s", key_file_path)
    with _open_key_file(str(key_file_path)) as key_file:
        key_json = json.load(key_file)
        return "localhost:" + key_json["InsecurePort"]


def _get_key_file_path(cluster_id: typing.Optional[str] = None) -> pathlib.Path:
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

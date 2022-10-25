""" Contains API to register and un-register measurement service with discovery service.
"""
import json
import logging
import pathlib
import os
import platform
import typing

import grpc

from ni_measurement_service._internal.stubs.ni.measurements.discovery.v1 import (
    discovery_service_pb2,
)
from ni_measurement_service._internal.stubs.ni.measurements.discovery.v1 import (
    discovery_service_pb2_grpc,
)
from ni_measurement_service.measurement.info import MeasurementInfo
from ni_measurement_service.measurement.info import ServiceInfo

if platform.system() == "Windows":
    import msvcrt
    import win32con
    import win32file


_PROVIDED_MEASUREMENT_SERVICE = "ni.measurements.v1.MeasurementService"

_logger = logging.getLogger(__name__)


class DiscoveryClient:
    """Class that contains APIs need to interact with discovery service.

    Attributes
    ----------
        stub (DiscoveryServiceStub): The gRPC stub to interact with discovery
        service.

        registration_id(string): The ID from discovery service upon successful registration.

    """

    def __init__(self, stub: discovery_service_pb2_grpc.DiscoveryServiceStub = None):
        """Initialise the Discovery Client with provided registry service stub.

        Args:
        ----
            stub (DiscoveryServiceStub, optional): The gRPC stub to interact with discovery
            service.Defaults to None.

        """
        channel = grpc.insecure_channel(_get_discovery_service_address())
        self.stub = stub or discovery_service_pb2_grpc.DiscoveryServiceStub(channel)
        self.registration_id = ""

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
        except (grpc._channel._InactiveRpcError):
            _logger.error(
                "Unable to register with discovery service. Possible reason: discovery service not available."
            )
            return False
        except (Exception):
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
        except (grpc._channel._InactiveRpcError):
            _logger.error(
                "Unable to unregister with discovery service. Possible reason: discovery service not available."
            )
            return False
        except (Exception):
            _logger.exception("Error in un-registering with discovery service.")
            return False
        return True


def _get_discovery_service_address() -> str:
    key_file_path = _get_key_file_path()
    try:
        with _open_key_file(str(key_file_path)) as key_file:
            key_json = json.load(key_file)
            return "localhost:" + key_json["InsecurePort"]
    except Exception as e:
        raise RuntimeError("Failed to read discovery service port number. Ensure the discovery service is running.") from e


def _get_key_file_path(cluster_id: typing.Optional[str] = None) -> pathlib.Path:
    if cluster_id is not None:
        return _get_key_file_directory() / f"DiscoveryService_{cluster_id}.json"
    return _get_key_file_directory() / "DiscoveryService.json"


def _get_key_file_directory() -> pathlib.Path:
    if platform.system() == "Windows":
        return (
            pathlib.Path(os.getenv("ProgramData"))
            / "National Instruments"
            / "Measurement Framework"
            / "Discovery"
            / "v1"
        )
    else:
        raise NotImplementedError("Platform not supported")


def _open_key_file(path: str) -> typing.TextIO:
    if platform.system() == "Windows":
        # Use the Win32 API to specify the share mode. Otherwise, opening the file throws PermissionError due to a sharing violation.
        # This is a workaround for https://github.com/python/cpython/issues/59449 (Support for opening files with FILE_SHARE_DELETE on Windows).
        fh = win32file.CreateFile(
            str(path),
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        fd = msvcrt.open_osfhandle(fh.handle, os.O_RDONLY | os.O_TEXT)
        fh.Detach()
        return os.fdopen(fd, "r", encoding="utf-8-sig")
    else:
        return open(path, "r")

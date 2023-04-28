"""Helper classes and functions for MeasurementLink examples."""

import logging
import pathlib
from typing import Any, Dict, NamedTuple, TypeVar

import grpc

from ni_measurementlink_service import session_management
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pinmap.v1 import (
    pin_map_service_pb2,
    pin_map_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import GrpcChannelPool


class ServiceOptions(NamedTuple):
    """Service options specified on the command line."""

    use_grpc_device: bool = False
    grpc_device_address: str = ""

    use_simulation: bool = False


T = TypeVar("T")


def str_to_enum(mapping: Dict[str, T], value: str) -> T:
    """Convert a string to an enum (with improved error reporting)."""
    try:
        return mapping[value]
    except KeyError as e:
        logging.error("Unsupported enum value %s", value)
        raise grpc.RpcError(
            grpc.StatusCode.INVALID_ARGUMENT,
            f'Unsupported enum value "{value}"',
        ) from e


class PinMapClient(object):
    """Class that communicates with the pin map service."""

    def __init__(self, *, grpc_channel: grpc.Channel):
        """Initialize pin map client."""
        self._client: pin_map_service_pb2_grpc.PinMapServiceStub = (
            pin_map_service_pb2_grpc.PinMapServiceStub(grpc_channel)
        )

    def update_pin_map(self, pin_map_path: str) -> str:
        """Update registered pin map contents.

        Create and register a pin map if a pin map resource for the specified pin map id is not
        found.

        Args:
            pin_map_path: The file path of the pin map to register as a pin map resource.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        pin_map_path_obj = pathlib.Path(pin_map_path)
        # By convention, the pin map id is the .pinmap file path.
        request = pin_map_service_pb2.UpdatePinMapFromXmlRequest(
            pin_map_id=pin_map_path, pin_map_xml=pin_map_path_obj.read_text(encoding="utf-8")
        )
        response: pin_map_service_pb2.PinMap = self._client.UpdatePinMapFromXml(request)
        return response.pin_map_id


class GrpcChannelPoolHelper(GrpcChannelPool):
    """Class that manages gRPC channel lifetimes."""

    def __init__(self):
        """Initialize the GrpcChannelPool object."""
        super().__init__()
        self._discovery_client = DiscoveryClient()

    @property
    def pin_map_channel(self) -> grpc.Channel:
        """Return gRPC channel to pin map service."""
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface="ni.measurementlink.pinmap.v1.PinMapService",
                service_class="ni.measurementlink.pinmap.v1.PinMapService",
            ).insecure_address
        )

    @property
    def session_management_channel(self) -> grpc.Channel:
        """Return gRPC channel to session management service."""
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface=session_management.GRPC_SERVICE_INTERFACE_NAME,
                service_class=session_management.GRPC_SERVICE_CLASS,
            ).insecure_address
        )

    def get_grpc_device_channel(self, provided_interface: str) -> grpc.Channel:
        """Return gRPC channel to specified NI gRPC Device service.

        Args:
            provided_interface (str): The gRPC Full Name of the service.

        """
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface=provided_interface,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            ).insecure_address
        )


class TestStandSupport(object):
    """Class that communicates with TestStand."""

    def __init__(self, sequence_context: Any) -> None:
        """Initialize the TestStandSupport object.

        Args:
            sequence_context:
                The SequenceContext COM object from the TestStand sequence execution.
                (Dynamically typed.)
        """
        self._sequence_context = sequence_context

    def get_active_pin_map_id(self) -> str:
        """Get the active pin map id from the NI.MeasurementLink.PinMapId temporary global variable.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        return self._sequence_context.Engine.TemporaryGlobals.GetValString(
            "NI.MeasurementLink.PinMapId", 0x0
        )

    def set_active_pin_map_id(self, pin_map_id: str) -> None:
        """Set the NI.MeasurementLink.PinMapId temporary global variable to the specified id.

        Args:
            pin_map_id:
                The resource id of the pin map that is registered to the pin map service.
        """
        self._sequence_context.Engine.TemporaryGlobals.SetValString(
            "NI.MeasurementLink.PinMapId", 0x1, pin_map_id
        )

    def resolve_file_path(self, file_path: str) -> str:
        """Resolve the absolute path to a file using the TestStand search directories.

        Args:
            file_path:
                An absolute or relative path to the file. If this is a relative path, this function
                searches the TestStand search directories for it.

        Returns:
            The absolute path to the file.
        """
        if pathlib.Path(file_path).is_absolute():
            return file_path
        (_, absolute_path, _, _, user_canceled) = self._sequence_context.Engine.FindFileEx(
            fileToFind=file_path,
            absolutePath=None,
            srchDirType=None,
            searchDirectoryIndex=None,
            userCancelled=None,  # Must match spelling used by TestStand
            searchContext=self._sequence_context.SequenceFile,
        )
        if user_canceled:
            raise RuntimeError("File lookup canceled by user.")
        return absolute_path

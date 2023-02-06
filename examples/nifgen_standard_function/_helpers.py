"""Helper classes and functions for MeasurementLink examples."""

import logging
import pathlib
from typing import Dict, NamedTuple, TypeVar

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

    def update_pin_map(self, pin_map_id: str) -> None:
        """Update registered pin map contents.

        Create and register a pin map if a pin map resource for the specified pin map id is not
        found.

        Args:
            pin_map_id (str): The resource id of the pin map to register as a pin map resource. By
                convention, the pin map id is the .pinmap file path.

        """
        pin_map_path = pathlib.Path(pin_map_id)
        request = pin_map_service_pb2.UpdatePinMapFromXmlRequest(
            pin_map_id=pin_map_id, pin_map_xml=pin_map_path.read_text(encoding="utf-8")
        )
        response: pin_map_service_pb2.PinMap = self._client.UpdatePinMapFromXml(request)
        assert response.pin_map_id == pin_map_id


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

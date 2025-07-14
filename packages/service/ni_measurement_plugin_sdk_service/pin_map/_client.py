"""Client for accessing the NI Pin Map Service."""

from __future__ import annotations

import logging
import pathlib
import threading

import grpc

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.pinmap.v1 import (
    pin_map_service_pb2,
    pin_map_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool

_logger = logging.getLogger(__name__)

GRPC_SERVICE_INTERFACE_NAME = "ni.measurementlink.pinmap.v1.PinMapService"
GRPC_SERVICE_CLASS = "ni.measurementlink.pinmap.v1.PinMapService"


class PinMapClient:
    """Client for accessing the NI Pin Map Service."""

    def __init__(
        self,
        *,
        discovery_client: DiscoveryClient | None = None,
        grpc_channel: grpc.Channel | None = None,
        grpc_channel_pool: GrpcChannelPool | None = None,
    ) -> None:
        """Initialize the pin map client.

        Args:
            discovery_client: An optional discovery client (recommended).

            grpc_channel: An optional pin map gRPC channel.

            grpc_channel_pool: An optional gRPC channel pool (recommended).
        """
        self._initialization_lock = threading.Lock()
        self._discovery_client = discovery_client
        self._grpc_channel_pool = grpc_channel_pool
        self._stub: pin_map_service_pb2_grpc.PinMapServiceStub | None = None

        if grpc_channel is not None:
            self._stub = pin_map_service_pb2_grpc.PinMapServiceStub(grpc_channel)

    def _get_stub(self) -> pin_map_service_pb2_grpc.PinMapServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    _logger.debug("Creating unshared GrpcChannelPool.")
                    self._grpc_channel_pool = GrpcChannelPool()
                if self._discovery_client is None:
                    _logger.debug("Creating unshared DiscoveryClient.")
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._grpc_channel_pool
                    )
                if self._stub is None:
                    compute_nodes = self._discovery_client.enumerate_compute_nodes()
                    remote_compute_nodes = [node for node in compute_nodes if not node.is_local]
                    # Use remote node URL as deployment target if only one remote node is found.
                    # If more than one remote node exists, use empty string for deployment target.
                    first_remote_node_url = (
                        remote_compute_nodes[0].url if len(remote_compute_nodes) == 1 else ""
                    )
                    service_location = self._discovery_client.resolve_service(
                        provided_interface=GRPC_SERVICE_INTERFACE_NAME,
                        deployment_target=first_remote_node_url,
                        service_class=GRPC_SERVICE_CLASS,
                    )
                    channel = self._grpc_channel_pool.get_channel(service_location.insecure_address)
                    self._stub = pin_map_service_pb2_grpc.PinMapServiceStub(channel)
        return self._stub

    def update_pin_map(self, pin_map_path: str | pathlib.Path) -> str:
        """Update registered pin map contents.

        Create and register a pin map if a pin map resource for the specified pin map id is not
        found.

        Args:
            pin_map_path: The file path of the pin map to register as a pin map resource.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        # By convention, the pin map id is the .pinmap file path.
        request = pin_map_service_pb2.UpdatePinMapFromXmlRequest(
            pin_map_id=str(pin_map_path),
            pin_map_xml=pathlib.Path(pin_map_path).read_text(encoding="utf-8-sig"),
        )
        response = self._get_stub().UpdatePinMapFromXml(request)
        return response.pin_map_id

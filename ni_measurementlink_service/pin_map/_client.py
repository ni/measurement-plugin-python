import logging
import threading
from typing import Optional

from ni_measurementlink_service._internal.stubs.ni.measurementlink.pinmap.v1 import (
    pin_map_service_pb2,
    pin_map_service_pb2_grpc,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool

GRPC_SERVICE_INTERFACE_NAME = "ni.measurementlink.pinmap.v1.PinMapService"
GRPC_SERVICE_CLASS = "ni.measurementlink.pinmap.v1.PinMapService"


_logger = logging.getLogger(__name__)


class PinMapClient:
    """Client for accessing the MeasurementLink pin map service."""

    def __init__(
        self,
        *,
        discovery_client: Optional[DiscoveryClient] = None,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ) -> None:
        """Initialize pin map client.

        Args:
            discovery_client: Discovery client.
            grpc_channel_pool: Grpc Channel pool.
        """
        self._initialization_lock = threading.Lock()
        self._discovery_client = discovery_client
        self._grpc_channel_pool = grpc_channel_pool
        self._stub: Optional[pin_map_service_pb2_grpc.PinMapServiceStub] = None

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
                    service_location = self._discovery_client.resolve_service(
                        provided_interface=GRPC_SERVICE_INTERFACE_NAME,
                        service_class=GRPC_SERVICE_CLASS,
                    )
                    channel = self._grpc_channel_pool.get_channel(service_location.insecure_address)
                    self._stub = pin_map_service_pb2_grpc.PinMapServiceStub(channel)
        return self._stub

    def update_pin_map(self, pin_map_path: str) -> str:
        """Registers or updates the pin map path.

        Args:
            pin_map_path: Pin map path.

        Returns:
            Pin map id.
        """
        with open(pin_map_path, "r") as file:
            xml_content = file.read()
        request = pin_map_service_pb2.UpdatePinMapFromXmlRequest(
            pin_map_id=pin_map_path, pin_map_xml=xml_content[3:]
        )
        response = self._get_stub().UpdatePinMapFromXml(request=request)

        return response.pin_map_id

"""Shared functions for interacting with NI gRPC Device Server."""
from __future__ import annotations

from typing import Optional

import grpc

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._configuration import (
    GRPC_DEVICE_ADDRESS,
    USE_GRPC_DEVICE_SERVER,
)
from ni_measurementlink_service.discovery import DiscoveryClient

SERVICE_CLASS = "ni.measurementlink.v1.grpcdeviceserver"
"""The service class for NI gRPC Device Server."""


def get_insecure_grpc_device_channel(
    discovery_client: DiscoveryClient,
    grpc_channel_pool: GrpcChannelPool,
    provided_interface: str,
) -> Optional[grpc.Channel]:
    """Get an unencrypted gRPC channel targeting NI gRPC Device Server.

    Args:
        discovery_client: The discovery client.

        grpc_channel_pool: The gRPC channel pool.

        provided_interface: The driver API's NI gRPC Device Server interface
        name.

    Returns:
        A gRPC channel targeting the NI gRPC Device Server, or ``None`` if the
        configuration file specifies that ``USE_GRPC_DEVICE_SERVER`` is false.
    """
    if not USE_GRPC_DEVICE_SERVER:
        return None

    address = GRPC_DEVICE_ADDRESS
    if not address:
        service_location = discovery_client.resolve_service(
            provided_interface=provided_interface,
            service_class=SERVICE_CLASS,
        )
        address = service_location.insecure_address

    return grpc_channel_pool.get_channel(address)

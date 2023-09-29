"""Shared functions for interacting with NI gRPC Device Server."""
from __future__ import annotations

import grpc

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._configuration import GRPC_DEVICE_ADDRESS
from ni_measurementlink_service._drivers import DriverModule
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient

SERVICE_CLASS = "ni.measurementlink.v1.grpcdeviceserver"
"""The service class for NI gRPC Device Server."""


def get_insecure_grpc_device_channel(
    discovery_client: DiscoveryClient,
    grpc_channel_pool: GrpcChannelPool,
    driver_module: DriverModule,
) -> grpc.Channel:
    """Get an unencrypted gRPC channel targeting NI gRPC Device Server for a specific driver API.

    Args:
        discovery_client: The discovery client.
        grpc_channel_pool: The gRPC channel pool.
        driver_module: The driver API module (e.g. ``nidcpower`` or ``nidaqmx``).

    Returns:
        A gRPC channel targeting the NI gRPC Device Server.
    """
    if not isinstance(driver_module, DriverModule):
        raise TypeError(f"Invalid driver module: {driver_module:r}")

    address = GRPC_DEVICE_ADDRESS
    if not address:
        service_location = discovery_client.resolve_service(
            provided_interface=driver_module.GRPC_SERVICE_INTERFACE_NAME,
            service_class=SERVICE_CLASS,
        )
        address = service_location.insecure_address

    return grpc_channel_pool.get_channel(address)

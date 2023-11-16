"""Shared functions for interacting with NI gRPC Device Server."""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

import grpc

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._configuration import (
    GRPC_DEVICE_SERVER_ADDRESS,
    USE_GRPC_DEVICE_SERVER,
)
from ni_measurementlink_service.discovery import DiscoveryClient

_logger = logging.getLogger(__name__)

SERVICE_CLASS = "ni.measurementlink.v1.grpcdeviceserver"
"""The service class for NI gRPC Device Server."""


def get_insecure_grpc_device_address(
    discovery_client: DiscoveryClient,
    provided_interface: str,
) -> str:
    """Get an address targeting NI gRPC Device Server for unencrypted communication."""
    if not USE_GRPC_DEVICE_SERVER:
        _logger.debug("Not using NI gRPC Device Server")
        return ""

    if GRPC_DEVICE_SERVER_ADDRESS:
        parsed_address = urlparse(GRPC_DEVICE_SERVER_ADDRESS)
        if parsed_address.scheme != "http":
            raise ValueError(
                f"Unsupported URL scheme '{parsed_address.scheme}'"
                f" for GRPC_DEVICE_SERVER_ADDRESS '{GRPC_DEVICE_SERVER_ADDRESS}'"
            )
        if (
            parsed_address.path not in ("", "/")
            or parsed_address.params
            or parsed_address.query
            or parsed_address.fragment
        ):
            raise ValueError(
                f"Unsupported GRPC_DEVICE_SERVER_ADDRESS '{GRPC_DEVICE_SERVER_ADDRESS}'"
            )
        address = parsed_address.netloc
        _logger.debug("Using NI gRPC Device Server with configured insecure address '%s'", address)
        return address

    service_location = discovery_client.resolve_service(
        provided_interface=provided_interface,
        service_class=SERVICE_CLASS,
    )
    address = service_location.insecure_address
    _logger.debug("Using NI gRPC Device Server with discovered insecure address '%s'", address)
    return address


def get_insecure_grpc_device_channel(
    discovery_client: DiscoveryClient,
    grpc_channel_pool: GrpcChannelPool,
    provided_interface: str,
) -> Optional[grpc.Channel]:
    """Get an unencrypted gRPC channel targeting NI gRPC Device Server."""
    address = get_insecure_grpc_device_address(discovery_client, provided_interface)
    if address:
        return grpc_channel_pool.get_channel(address)
    else:
        return None

"""Shared functions for interacting with NI gRPC Device Server."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlsplit

import grpc

from ni_measurementlink_service._configuration import (
    GRPC_DEVICE_SERVER_ADDRESS,
    USE_GRPC_DEVICE_SERVER,
)
from ni_measurementlink_service.discovery import DiscoveryClient, ServiceLocation
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool

_logger = logging.getLogger(__name__)

SERVICE_CLASS = "ni.measurementlink.v1.grpcdeviceserver"
"""The service class for NI gRPC Device Server."""


def get_grpc_device_server_location(
    discovery_client: DiscoveryClient,
    provided_interface: str,
) -> Optional[ServiceLocation]:
    """Get an address targeting NI gRPC Device Server for unencrypted communication."""
    if not USE_GRPC_DEVICE_SERVER:
        _logger.debug("Not using NI gRPC Device Server")
        return None

    if GRPC_DEVICE_SERVER_ADDRESS:
        service_location = _parse_url_to_service_location(GRPC_DEVICE_SERVER_ADDRESS)
        _logger.debug(
            "NI gRPC Device Server location (from GRPC_DEVICE_SERVER_ADDRESS): %r", service_location
        )
        return service_location

    service_location = discovery_client.resolve_service(
        provided_interface=provided_interface,
        service_class=SERVICE_CLASS,
    )
    _logger.debug(
        "NI gRPC Device Server location (for interface '%s'): %r",
        provided_interface,
        service_location,
    )
    return service_location


def _parse_url_to_service_location(url: str) -> ServiceLocation:
    parsed_url = urlsplit(url)

    if parsed_url.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme '{parsed_url.scheme}' in '{url}'")
    if parsed_url.path not in ("", "/"):
        raise ValueError(f"Unsupported path '{parsed_url.path}' in '{url}'")
    if parsed_url.query:
        raise ValueError(f"Unsupported query '?{parsed_url.query}' in '{url}'")
    if parsed_url.fragment:
        raise ValueError(f"Unsupported fragment '#{parsed_url.fragment}' in '{url}'")
    if parsed_url.hostname is None:
        raise ValueError(f"No host specified in '{url}'")
    if parsed_url.port is None:
        raise ValueError(f"No port number specified in '{url}'")

    host = parsed_url.hostname
    port = str(parsed_url.port)
    if "[" in parsed_url.netloc and "]" in parsed_url.netloc:
        # Preserve IPv6 address brackets
        host = "[" + host + "]"

    if parsed_url.scheme == "http":
        return ServiceLocation(location=host, insecure_port=port, ssl_authenticated_port="")
    else:
        return ServiceLocation(location=host, insecure_port="", ssl_authenticated_port=port)


def get_insecure_grpc_device_server_channel(
    discovery_client: DiscoveryClient,
    grpc_channel_pool: GrpcChannelPool,
    provided_interface: str,
) -> Optional[grpc.Channel]:
    """Get an unencrypted gRPC channel targeting NI gRPC Device Server."""
    service_location = get_grpc_device_server_location(discovery_client, provided_interface)
    if not service_location:
        return None
    if not service_location.insecure_port:
        raise ValueError(f"No insecure port specified in {service_location!r}")
    return grpc_channel_pool.get_channel(service_location.insecure_address)

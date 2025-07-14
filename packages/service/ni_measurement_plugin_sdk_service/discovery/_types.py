"""Data types for the NI Discovery Service."""

from __future__ import annotations

import typing

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
)


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

    @classmethod
    def _from_grpc(cls, other: discovery_service_pb2.ServiceLocation) -> ServiceLocation:
        return ServiceLocation(
            location=other.location,
            insecure_port=other.insecure_port,
            ssl_authenticated_port=other.ssl_authenticated_port,
        )


class ComputeNodeDescriptor(typing.NamedTuple):
    """Represents a compute node."""

    url: str
    """The resolvable name (URL) of the compute node."""

    is_local: bool
    """Indicates whether the compute node is local node."""

    @classmethod
    def _from_grpc(
        cls, other: discovery_service_pb2.ComputeNodeDescriptor
    ) -> ComputeNodeDescriptor:
        return ComputeNodeDescriptor(
            url=other.url,
            is_local=other.is_local,
        )

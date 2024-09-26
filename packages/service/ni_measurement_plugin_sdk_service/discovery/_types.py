"""Data types for the NI Discovery Service."""

import typing

from ni_measurement_plugin_sdk_service.measurement.info import ServiceInfo


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


class ResolveServiceWithInformationResponse(typing.NamedTuple):
    """Represents the location of a service along with its information."""

    service_location: ServiceLocation
    service_info: ServiceInfo

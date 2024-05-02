"""Data types for the MeasurementLink discovery service."""

from typing import Dict, Iterable, NamedTuple


class ServiceDescriptor(NamedTuple):
    """Represents the service."""

    display_name: str
    description_url: str
    provided_interfaces: Iterable[str]
    service_class: str
    annotations: Dict[str, str]


class ServiceLocation(NamedTuple):
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

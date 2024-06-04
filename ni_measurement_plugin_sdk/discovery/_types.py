"""Data types for the MeasurementLink discovery service."""

import typing


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

"""Public API for accessing the MeasurementLink discovery service."""

from ni_measurementlink_service.discovery._client import DiscoveryClient
from ni_measurementlink_service.discovery._types import (
    ServiceDescriptor,
    ServiceLocation,
)

__all__ = ["DiscoveryClient", "ServiceDescriptor", "ServiceLocation"]

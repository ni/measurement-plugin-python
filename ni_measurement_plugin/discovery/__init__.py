"""Public API for accessing the MeasurementLink discovery service."""

from ni_measurement_plugin.discovery._client import DiscoveryClient
from ni_measurement_plugin.discovery._types import ServiceLocation

__all__ = ["DiscoveryClient", "ServiceLocation"]

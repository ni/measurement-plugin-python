"""Public API for accessing the MeasurementLink discovery service."""

from ni_measurement_plugin_sdk.discovery._client import DiscoveryClient
from ni_measurement_plugin_sdk.discovery._types import ServiceLocation

__all__ = ["DiscoveryClient", "ServiceLocation"]

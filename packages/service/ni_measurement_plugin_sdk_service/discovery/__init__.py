"""Public API for accessing the NI Discovery Service."""

from ni_measurement_plugin_sdk_service.discovery._client import DiscoveryClient
from ni_measurement_plugin_sdk_service.discovery._types import (
    ComputeNodeDescriptor,
    ServiceLocation,
)

__all__ = ["DiscoveryClient", "ServiceLocation", "ComputeNodeDescriptor"]

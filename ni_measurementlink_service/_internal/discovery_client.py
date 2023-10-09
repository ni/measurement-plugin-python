"""Redirect internal discovery client API to the public API."""

import warnings

from deprecation import DeprecatedWarning

from ni_measurementlink_service.discovery._client import DiscoveryClient
from ni_measurementlink_service.discovery._types import ServiceLocation

__all__ = ["DiscoveryClient", "ServiceLocation"]

warnings.warn(
    DeprecatedWarning(
        "ni_measurementlink_service._internal.discovery_client",
        deprecated_in="1.3.0",
        removed_in=None,
        details="Use ni_measurementlink_service.discovery instead.",
    ),
)

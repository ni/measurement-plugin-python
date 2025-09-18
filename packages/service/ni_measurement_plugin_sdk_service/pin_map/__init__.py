"""Compatibility API for accessing the NI Pin Map Service.

The public API for accessing the NI Pin Map Service has moved to the
:mod:`ni.measurementlink.pinmap.v1.client` package.

The :mod:`ni_measurement_plugin_sdk_service.pin_map` subpackage provides
compatibility with existing applications and will be deprecated in a future
release.
"""

from ni.measurementlink.pinmap.v1.client import PinMapClient

__all__ = ["PinMapClient"]

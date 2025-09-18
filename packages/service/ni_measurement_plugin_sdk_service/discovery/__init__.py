"""Compatibility API for accessing the NI Discovery Service.

The public API for accessing the NI Discovery Service has moved to the
:mod:`ni.measurementlink.discovery.v1.client` package.

The :mod:`ni_measurement_plugin_sdk_service.discovery` subpackage provides
compatibility with existing applications and will be deprecated in a future
release.
"""

from ni.measurementlink.discovery.v1.client import DiscoveryClient, ServiceLocation

__all__ = ["DiscoveryClient", "ServiceLocation"]

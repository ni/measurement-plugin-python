"""Compatibility API for gRPC logging interceptors.

The gRPC logging interceptor classes have moved to the :mod:`ni_grpc_extensions`
package.

The :mod:`ni_measurement_plugin_sdk_service.grpc.loggers` submodule provides
compatibility with existing applications and will be deprecated in a future
release.
"""

from ni_grpc_extensions.loggers import ClientLogger, ServerLogger

__all__ = ["ClientLogger", "ServerLogger"]

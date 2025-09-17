"""Compatibility API for gRPC channel pool.

The :obj:`GrpcChannelPool` class has moved to the :mod:`ni_grpc_extensions`
package.

The :mod:`ni_measurement_plugin_sdk_service.grpc.channelpool` submodule provides
compatibility with existing applications and will be deprecated in a future
release.
"""

from ni_grpc_extensions.channelpool import GrpcChannelPool

__all__ = ["GrpcChannelPool"]

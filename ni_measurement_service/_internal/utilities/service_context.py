"""Contains Service Context class for context variable used with gRPC calls."""
from typing import Callable, Optional
import grpc

class ServiceContext:
    """Accessor for the Measurement Service's context-local state."""

    def __init__(self, grpc_context: grpc.ServicerContext):
        """Initialize the Measurement Service Context."""
        self._grpc_context: grpc.ServicerContext = grpc_context
        self._is_complete: bool = False
        self._exception: Optional[Exception] = None

    def mark_complete(self, exception: Optional[Exception] = None):
        """Mark the current RPC as complete."""
        self._is_complete = True
        self._exception = exception

    def add_cancel_callback(self, cancel_callback: Callable):
        """Add a callback that is invoked when the RPC is canceled."""

        def grpc_callback():
            if not self._is_complete:
                cancel_callback()

        self._grpc_context.add_callback(grpc_callback)
"""A throwable version of grpc.RpcError for testing."""

import grpc


class FakeRpcError(grpc.RpcError):
    """A throwable version of grpc.RpcError for testing."""

    def __init__(self, code: grpc.StatusCode, details: str) -> None:
        """Construct a FakeRpcError."""
        self._code = code
        self._details = details

    def code(self) -> grpc.StatusCode:
        """Get the gRPC status code."""
        return self._code

    def details(self) -> str:
        """Get the error details."""
        return self._details

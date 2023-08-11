from __future__ import annotations

try:
    import traceloggingdynamic

    _event_provider = traceloggingdynamic.Provider(b"NI-MeasurementLink-Python")
except ImportError:
    _event_provider = None

_LEVEL_LOG_ALWAYS = 0
_LEVEL_CRITICAL = 1
_LEVEL_ERROR = 3
_LEVEL_WARNING = 3
_LEVEL_INFO = 4
_LEVEL_VERBOSE = 5

_OPCODE_INFO = 0
_OPCODE_START = 1
_OPCODE_STOP = 2

_KEYWORD_NONE = 0
_KEYWORD_GRPC = 1 << 0

_TASK_GRPC_CLIENT_CALL = 1
_TASK_GRPC_SERVER_CALL = 2

_ID_GRPC_CLIENT_CALL_START = 1
_ID_GRPC_CLIENT_CALL_STOP = 2
_ID_GRPC_CLIENT_CALL_STREAMING_REQUEST = 3
_ID_GRPC_CLIENT_CALL_STREAMING_RESPONSE = 4
_ID_GRPC_SERVER_CALL_START = 5
_ID_GRPC_SERVER_CALL_STOP = 6
_ID_GRPC_SERVER_CALL_STREAMING_REQUEST = 7
_ID_GRPC_SERVER_CALL_STREAMING_RESPONSE = 8


def is_enabled() -> bool:
    """Queries whether the event provider is enabled."""
    return _event_provider and _event_provider.is_enabled()


# TODO: does traceloggingdynamic support a formatted message template like .NET EventSource does?
# TODO: figure out how to use activity id correctly. Do I need to call EventActivityIdControl?
def log_grpc_client_call_start(method_name: str) -> None:
    """Log when starting a gRPC client call."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStart",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            id=_ID_GRPC_CLIENT_CALL_START,
            task=_TASK_GRPC_CLIENT_CALL,
        )
        eb.add_str8(b"Message", "gRPC client call starting: " + method_name)
        _event_provider.write(eb)


def log_grpc_client_call_stop(method_name: str) -> None:
    """Log when a gRPC client call has completed."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStop",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_STOP,
            id=_ID_GRPC_CLIENT_CALL_STOP,
            task=_TASK_GRPC_CLIENT_CALL,
        )
        eb.add_str8(b"Message", "gRPC client call starting: " + method_name)
        _event_provider.write(eb)


def log_grpc_client_call_streaming_request(method_name: str) -> None:
    """Log when a gRPC client call is sending a client-streaming request."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStreamingRequest",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
            id=_ID_GRPC_CLIENT_CALL_STREAMING_REQUEST,
        )
        eb.add_str8(b"Message", "gRPC client call streaming request: " + method_name)
        _event_provider.write(eb)


def log_grpc_client_call_streaming_response(method_name: str) -> None:
    """Log when a gRPC client call has received a server-streaming response."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStreamingResponse",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            id=_ID_GRPC_CLIENT_CALL_STREAMING_RESPONSE,
        )
        eb.add_str8(b"Message", "gRPC client call streaming response: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_start(method_name: str) -> None:
    """Log when starting a gRPC server call."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStart",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            id=_ID_GRPC_SERVER_CALL_START,
            task=_TASK_GRPC_SERVER_CALL,
        )
        eb.add_str8(b"Message", "gRPC server call starting: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_stop(method_name: str) -> None:
    """Log when a gRPC server call has completed."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStop",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_STOP,
            id=_ID_GRPC_SERVER_CALL_STOP,
            task=_TASK_GRPC_SERVER_CALL,
        )
        eb.add_str8(b"Message", "gRPC server call starting: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_streaming_request(method_name: str) -> None:
    """Log when a gRPC server call is sending a server-streaming request."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStreamingRequest",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
            id=_ID_GRPC_SERVER_CALL_STREAMING_REQUEST,
        )
        eb.add_str8(b"Message", "gRPC server call streaming request: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_streaming_response(method_name: str) -> None:
    """Log when a gRPC server call has received a server-streaming response."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStreamingResponse",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            id=_ID_GRPC_SERVER_CALL_STREAMING_RESPONSE,
        )
        eb.add_str8(b"Message", "gRPC server call streaming response: " + method_name)
        _event_provider.write(eb)

from __future__ import annotations

import ctypes
import sys
import uuid
from typing import Optional

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


if sys.platform == "win32":
    # 0x00000800 = LOAD_LIBRARY_SEARCH_SYSTEM32 (Win8 or later)
    _eventing_dll = ctypes.WinDLL("api-ms-win-eventing-provider-l1-1-0.dll", mode=0x00000800)

    _EventActivityIdControl = _eventing_dll.EventActivityIdControl
    _EventActivityIdControl.restype = ctypes.c_uint32
    _EventActivityIdControl.argtypes = (ctypes.c_uint32, ctypes.c_void_p)

    _EVENT_ACTIVITY_CTRL_GET_ID = 1
    _EVENT_ACTIVITY_CTRL_SET_ID = 2
    _EVENT_ACTIVITY_CTRL_CREATE_ID = 3
    _EVENT_ACTIVITY_CTRL_GET_SET_ID = 4
    _EVENT_ACTIVITY_CTRL_CREATE_SET_ID = 5

    def _create_activity_id() -> uuid.UUID:
        activity_bytes = (ctypes.c_byte * 16)()
        status = _EventActivityIdControl(
            _EVENT_ACTIVITY_CTRL_CREATE_ID, ctypes.pointer(activity_bytes)
        )
        if status != 0:
            raise OSError("EventActivityIdControl error", status)
        return uuid.UUID(bytes_le=bytes(activity_bytes))

    def _get_current_thread_activity_id() -> uuid.UUID:
        activity_bytes = (ctypes.c_byte * 16)()
        status = _EventActivityIdControl(
            _EVENT_ACTIVITY_CTRL_GET_ID, ctypes.pointer(activity_bytes)
        )
        if status != 0:
            raise OSError("EventActivityIdControl error", status)
        return uuid.UUID(bytes_le=bytes(activity_bytes))

else:

    def _create_activity_id() -> uuid.UUID:
        return uuid.uuid4()

    def _get_current_thread_activity_id() -> uuid.UUID:
        return uuid.UUID()


def is_enabled() -> bool:
    """Queries whether the event provider is enabled."""
    return _event_provider and _event_provider.is_enabled()


def log_grpc_client_call_start(method_name: str) -> Optional[uuid.UUID]:
    """Log when starting a gRPC client call."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCall",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            task=_TASK_GRPC_CLIENT_CALL,
        )
        eb.add_str8(b"FormattedMessage", "gRPC client call starting: " + method_name)
        activity_id = _create_activity_id()
        related_activity_id = _get_current_thread_activity_id()
        _event_provider.write(eb, activity_id, related_activity_id)
        return activity_id
    else:
        return None


def log_grpc_client_call_stop(method_name: str, activity_id: Optional[uuid.UUID] = None) -> None:
    """Log when a gRPC client call has completed."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCall",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_STOP,
            task=_TASK_GRPC_CLIENT_CALL,
        )
        eb.add_str8(b"FormattedMessage", "gRPC client call complete: " + method_name)
        _event_provider.write(eb, activity_id)


def log_grpc_client_call_streaming_request(method_name: str) -> None:
    """Log when a gRPC client call is sending a client-streaming request."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStreamingRequest",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
        )
        eb.add_str8(b"FormattedMessage", "gRPC client call streaming request: " + method_name)
        _event_provider.write(eb)


def log_grpc_client_call_streaming_response(method_name: str) -> None:
    """Log when a gRPC client call has received a server-streaming response."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcClientCallStreamingResponse",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
        )
        eb.add_str8(b"FormattedMessage", "gRPC client call streaming response: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_start(method_name: str) -> Optional[uuid.UUID]:
    """Log when starting a gRPC server call."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCall",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_START,
            task=_TASK_GRPC_SERVER_CALL,
        )
        eb.add_str8(b"FormattedMessage", "gRPC server call starting: " + method_name)
        activity_id = _create_activity_id()
        related_activity_id = _get_current_thread_activity_id()
        _event_provider.write(eb, activity_id, related_activity_id)
        return activity_id
    else:
        return None


def log_grpc_server_call_stop(method_name: str, activity_id: Optional[uuid.UUID] = None) -> None:
    """Log when a gRPC server call has completed."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCall",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_STOP,
            task=_TASK_GRPC_SERVER_CALL,
        )
        eb.add_str8(b"FormattedMessage", "gRPC server call complete: " + method_name)
        _event_provider.write(eb, activity_id)


def log_grpc_server_call_streaming_request(method_name: str) -> None:
    """Log when a gRPC server call is sending a server-streaming request."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStreamingRequest",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
        )
        eb.add_str8(b"FormattedMessage", "gRPC server call streaming request: " + method_name)
        _event_provider.write(eb)


def log_grpc_server_call_streaming_response(method_name: str) -> None:
    """Log when a gRPC server call has received a server-streaming response."""
    if _event_provider and _event_provider.is_enabled(level=_LEVEL_INFO, keyword=_KEYWORD_GRPC):
        eb = traceloggingdynamic.EventBuilder()
        eb.reset(
            b"GrpcServerCallStreamingResponse",
            level=_LEVEL_INFO,
            keyword=_KEYWORD_GRPC,
            opcode=_OPCODE_INFO,
        )
        eb.add_str8(b"FormattedMessage", "gRPC server call streaming response: " + method_name)
        _event_provider.write(eb)

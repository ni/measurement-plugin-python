from __future__ import annotations
import copy
import ctypes
import threading
import sys
import uuid
from typing import Dict, List

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

if sys.platform == "win32":
    # 0x00000800 = LOAD_LIBRARY_SEARCH_SYSTEM32 (Win8 or later)
    _eventing_dll = ctypes.WinDLL('api-ms-win-eventing-provider-l1-1-0.dll', mode = 0x00000800)

    _EventActivityIdControl = _eventing_dll.EventActivityIdControl
    _EventActivityIdControl.restype = ctypes.c_uint32
    _EventActivityIdControl.argtypes = (ctypes.c_uint32, ctypes.c_void_p)

    _EVENT_ACTIVITY_CTRL_GET_ID = 1
    _EVENT_ACTIVITY_CTRL_SET_ID = 2
    _EVENT_ACTIVITY_CTRL_CREATE_ID = 3
    _EVENT_ACTIVITY_CTRL_GET_SET_ID = 4
    _EVENT_ACTIVITY_CTRL_CREATE_SET_ID = 5

    _parent_activity_id_map: Dict[uuid.UUID, uuid.UUID] = {}
    _parent_activity_id_map_lock = threading.Lock()

    _UUIDBytes = ctypes.c_byte * 16

    def _start_activity() -> (uuid.UUID, uuid.UUID):
        new_activity_bytes = _UUIDBytes()
        status = _EventActivityIdControl(_EVENT_ACTIVITY_CTRL_CREATE_ID, ctypes.pointer(new_activity_bytes))
        assert status == 0
        parent_activity_bytes = _UUIDBytes(*new_activity_bytes)
        status = _EventActivityIdControl(_EVENT_ACTIVITY_CTRL_GET_SET_ID, ctypes.pointer(parent_activity_bytes))
        assert status == 0
        new_activity_id = uuid.UUID(bytes_le=bytes(new_activity_bytes))
        parent_activity_id = uuid.UUID(bytes_le=bytes(parent_activity_bytes))
        with _parent_activity_id_map_lock:
            _parent_activity_id_map[new_activity_id] = parent_activity_id
        print("start", parent_activity_id, new_activity_id)
        return (parent_activity_id, new_activity_id)

    def _stop_activity() -> uuid.UUID:
        old_activity_bytes = _UUIDBytes()
        status = _EventActivityIdControl(_EVENT_ACTIVITY_CTRL_GET_ID, ctypes.pointer(old_activity_bytes))
        assert status == 0
        old_activity_id = uuid.UUID(bytes_le=bytes(old_activity_bytes))
        with _parent_activity_id_map_lock:
            parent_activity_id = _parent_activity_id_map.pop(old_activity_id, None)
        if parent_activity_id is None:
            parent_activity_id = uuid.UUID(int=0)
        status = _EventActivityIdControl(_EVENT_ACTIVITY_CTRL_SET_ID, parent_activity_id.bytes_le)
        assert status == 0
        print("stop", parent_activity_id, old_activity_id)
        return old_activity_id

def is_enabled() -> bool:
    """Queries whether the event provider is enabled."""
    return _event_provider and _event_provider.is_enabled()

# TODO: does traceloggingdynamic support a formatted message template like .NET EventSource does?
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
        parent_activity_id, activity_id = _start_activity()
        _event_provider.write(eb, activity_id=activity_id, related_activity_id=parent_activity_id)


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
        activity_id = _stop_activity()
        _event_provider.write(eb, activity_id=activity_id)


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
        parent_activity_id, activity_id = _start_activity()
        _event_provider.write(eb, activity_id=activity_id, related_activity_id=parent_activity_id)


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
        activity_id = _stop_activity()
        _event_provider.write(eb, activity_id=activity_id)


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

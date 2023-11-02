from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Configurations(_message.Message):
    __slots__ = ["current_limit", "multi_session", "pin_names"]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    MULTI_SESSION_FIELD_NUMBER: _ClassVar[int]
    PIN_NAMES_FIELD_NUMBER: _ClassVar[int]
    current_limit: float
    multi_session: bool
    pin_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, pin_names: _Optional[_Iterable[str]] = ..., current_limit: _Optional[float] = ..., multi_session: bool = ...) -> None: ...

class Outputs(_message.Message):
    __slots__ = ["channel_lists", "connected_channels", "current_measurements", "resource_names", "session_names", "voltage_measurements"]
    CHANNEL_LISTS_FIELD_NUMBER: _ClassVar[int]
    CONNECTED_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_MEASUREMENTS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAMES_FIELD_NUMBER: _ClassVar[int]
    SESSION_NAMES_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_MEASUREMENTS_FIELD_NUMBER: _ClassVar[int]
    channel_lists: _containers.RepeatedScalarFieldContainer[str]
    connected_channels: _containers.RepeatedScalarFieldContainer[str]
    current_measurements: _containers.RepeatedScalarFieldContainer[float]
    resource_names: _containers.RepeatedScalarFieldContainer[str]
    session_names: _containers.RepeatedScalarFieldContainer[str]
    voltage_measurements: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, session_names: _Optional[_Iterable[str]] = ..., resource_names: _Optional[_Iterable[str]] = ..., channel_lists: _Optional[_Iterable[str]] = ..., connected_channels: _Optional[_Iterable[str]] = ..., voltage_measurements: _Optional[_Iterable[float]] = ..., current_measurements: _Optional[_Iterable[float]] = ...) -> None: ...

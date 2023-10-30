from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class NIDCPowerConfigurations(_message.Message):
    __slots__ = ["multi_session", "pin_names"]
    MULTI_SESSION_FIELD_NUMBER: _ClassVar[int]
    PIN_NAMES_FIELD_NUMBER: _ClassVar[int]
    multi_session: bool
    pin_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, pin_names: _Optional[_Iterable[str]] = ..., multi_session: bool = ...) -> None: ...

class NIDCPowerOutputs(_message.Message):
    __slots__ = ["channel_lists", "resource_names", "session_names"]
    CHANNEL_LISTS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAMES_FIELD_NUMBER: _ClassVar[int]
    SESSION_NAMES_FIELD_NUMBER: _ClassVar[int]
    channel_lists: _containers.RepeatedScalarFieldContainer[str]
    resource_names: _containers.RepeatedScalarFieldContainer[str]
    session_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, session_names: _Optional[_Iterable[str]] = ..., resource_names: _Optional[_Iterable[str]] = ..., channel_lists: _Optional[_Iterable[str]] = ...) -> None: ...

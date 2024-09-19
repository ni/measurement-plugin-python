from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

BLACK: ProtobufColor
DESCRIPTOR: _descriptor.FileDescriptor
NONE: ProtobufColor
PINK: ProtobufColor
WHITE: ProtobufColor

class ProtobufColor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

from typing import Any

from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from google.protobuf.type_pb2 import Field

_TYPE_DEFAULT_MAPPING = {
    Field.TYPE_FLOAT: float(),
    Field.TYPE_DOUBLE: float(),
    Field.TYPE_INT32: int(),
    Field.TYPE_INT64: int(),
    Field.TYPE_UINT32: int(),
    Field.TYPE_UINT64: int(),
    Field.TYPE_BOOL: bool(),
    Field.TYPE_STRING: str(),
    Field.TYPE_ENUM: int(),
}

TYPE_FIELD_MAPPING = {
    Field.TYPE_FLOAT: FieldDescriptorProto.TYPE_FLOAT,
    Field.TYPE_DOUBLE: FieldDescriptorProto.TYPE_DOUBLE,
    Field.TYPE_INT32: FieldDescriptorProto.TYPE_INT32,
    Field.TYPE_INT64: FieldDescriptorProto.TYPE_INT64,
    Field.TYPE_UINT32: FieldDescriptorProto.TYPE_UINT32,
    Field.TYPE_UINT64: FieldDescriptorProto.TYPE_UINT64,
    Field.TYPE_BOOL: FieldDescriptorProto.TYPE_BOOL,
    Field.TYPE_STRING: FieldDescriptorProto.TYPE_STRING,
    Field.TYPE_ENUM: FieldDescriptorProto.TYPE_ENUM,
    Field.TYPE_MESSAGE: FieldDescriptorProto.TYPE_MESSAGE,
}


def get_type_default(type: Field.Kind.ValueType, repeated: bool) -> Any:
    """Get the default value for the give type."""
    if repeated:
        return list()
    return _TYPE_DEFAULT_MAPPING.get(type)

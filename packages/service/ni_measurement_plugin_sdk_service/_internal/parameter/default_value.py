from typing import Any

from google.protobuf import type_pb2

_type_default_mapping = {
    type_pb2.Field.TYPE_FLOAT: float(),
    type_pb2.Field.TYPE_DOUBLE: float(),
    type_pb2.Field.TYPE_INT32: int(),
    type_pb2.Field.TYPE_INT64: int(),
    type_pb2.Field.TYPE_UINT32: int(),
    type_pb2.Field.TYPE_UINT64: int(),
    type_pb2.Field.TYPE_BOOL: bool(),
    type_pb2.Field.TYPE_STRING: str(),
    type_pb2.Field.TYPE_ENUM: int(),
}


def get_type_default(type: type_pb2.Field.Kind.ValueType, repeated: bool) -> Any:
    """Get the default value for the give type."""
    if repeated:
        return list()
    return _type_default_mapping.get(type)

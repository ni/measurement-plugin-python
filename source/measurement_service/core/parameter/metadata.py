import google.protobuf.type_pb2 as type_pb2
from typing import Any, NamedTuple


class ParameterMetadata(NamedTuple):
    display_name: str
    type: type_pb2.Field
    repeated: bool
    default_value: Any

from typing import ByteString, Dict, Iterable
import serializationstrategy
import google.protobuf.type_pb2 as type_pb2


class Parameter:
    def __init__(self, id, value):
        self.id = id
        self.value = value


class ParameterMetadata:
    def __init__(self, name: str, type: type_pb2.Field, repeated: bool):
        self.name = name
        self.type = type
        self.repeated = repeated


def deserialize_parameters(
    parametersMetadata: Dict[id, ParameterMetadata], parametersByteArray: ByteString
) -> Iterable[Parameter]:
    pass


def serialize_parameters(
    parameter_metadata: Dict[id, ParameterMetadata], parameterValue: Iterable[Parameter]
) -> ByteString:
    pass

import io
from typing import Dict
import serializationstrategy
import google.protobuf.type_pb2 as type_pb2
from google.protobuf.internal import encoder


class Parameter:
    def __init__(self, id, value):
        self.id = id
        self.value = value


class ParameterMetadata:
    def __init__(self, name: str, type: type_pb2.Field, repeated: bool):
        self.name = name
        self.type = type
        self.repeated = repeated


def deserialize_parameters(parameter_metadata_dict: Dict[id, ParameterMetadata], parameter_bytes):

    position = 0
    mapping = {}
    for key in parameter_metadata_dict:
        name = parameter_metadata_dict[key].name
        type = parameter_metadata_dict[key].type
        is_repeated = parameter_metadata_dict[key].repeated
        field_index = key
        serializer = serializationstrategy.Context.get_strategy(type, is_repeated)
        decoder = serializer.decoder(field_index, name)
        position = decoder(
            parameter_bytes,
            position + encoder._TagSize(field_index),
            parameter_bytes.__sizeof__(),
            type,
            mapping,
        )
    return mapping


def serialize_parameters(parameter_metadata_dict: Dict[id, ParameterMetadata], parameter_value):
    serialize_buffer = io.BytesIO()
    for i, parameter in enumerate(parameter_value):
        serializer = serializationstrategy.Context.get_strategy(
            parameter_metadata_dict[i + 1].type,
            parameter_metadata_dict[i + 1].repeated,
        )
        encoder = serializer.encoder(i + 1)
        encoder(serialize_buffer.write, parameter, None)
    return serialize_buffer.getvalue()

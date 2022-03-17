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
    mapping = {}  # inner_decoder update the mapping
    for key, value in parameter_metadata_dict.items():
        name = value.name
        type = value.type
        is_repeated = value.repeated
        field_index = key
        decoder = serializationstrategy.Context.get_decoder(type, is_repeated)
        inner_decoder = decoder(field_index, name)
        position = inner_decoder(
            parameter_bytes,
            position + encoder._TagSize(field_index),
            parameter_bytes.__sizeof__(),
            type,
            mapping,
        )
    return mapping


def serialize_parameters(parameter_metadata_dict: Dict[id, ParameterMetadata], parameter_value):
    serialize_buffer = io.BytesIO()  # inner_encoder updates the serialize_buffer
    for i, parameter in enumerate(parameter_value):
        encoder = serializationstrategy.Context.get_encoder(
            parameter_metadata_dict[i + 1].type,
            parameter_metadata_dict[i + 1].repeated,
        )
        inner_encoder = encoder(i + 1)
        inner_encoder(serialize_buffer.write, parameter, None)
    return serialize_buffer.getvalue()

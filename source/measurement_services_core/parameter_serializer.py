import io
from typing import ByteString, Dict, Iterable
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


def deserialize_parameters(
    parameter_metadata_dict: Dict[id, ParameterMetadata], parameters_byte_array: ByteString
) -> Iterable[Parameter]:

    position = 0
    mapping = {}
    parameter_list = []
    for parameter_info in parameter_metadata_dict:
        type = parameter_info.value.type
        is_repeated = parameter_info.value.repeated
        field_index = parameter_info.key
        serializer = serializationstrategy.Context.get_strategy(type, is_repeated)
        decoder = serializer.decoder(field_index, field_index)
        position = decoder(
            parameters_byte_array,
            position + encoder._TagSize(field_index),
            parameters_byte_array.__sizeof__(),
            type,
            mapping,
        )
    for item in mapping:
        parameter = Parameter(item.key, item.value)
        parameter_list.append(parameter)
    return parameter_list


def serialize_parameters(
    parameter_metadata_dict: Dict[id, ParameterMetadata], parameter_value: Iterable[Parameter]
) -> ByteString:
    serialize_buffer = io.BytesIO()
    for parameter in parameter_value:
        serializer = serializationstrategy.Context.get_strategy(
            parameter_metadata_dict[parameter.id].type,
            parameter_metadata_dict[parameter.id].repeated,
        )
        encoder = serializer.encoder(parameter.id)
        encoder(serialize_buffer, parameter.value)
    return serialize_buffer.getvalue()

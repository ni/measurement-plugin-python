import io
from typing import Dict
from google.protobuf.internal import encoder
from nimf.internal.parameter.metadata import ParameterMetadata
import nimf.internal.parameter.serializationstrategy as serializationstrategy


def deserialize_parameters(metadata_dict: Dict[id, ParameterMetadata], parameter_bytes):

    position = 0
    mapping_by_filed_index = {}  # inner_decoder update the mapping
    for key, value in metadata_dict.items():
        type = value.type
        is_repeated = value.repeated
        field_index = key
        decoder = serializationstrategy.Context.get_decoder(type, is_repeated)
        inner_decoder = decoder(field_index, field_index)
        position = inner_decoder(
            parameter_bytes,
            position + encoder._TagSize(field_index),
            parameter_bytes.__sizeof__(),
            type,
            mapping_by_filed_index,
        )
    return mapping_by_filed_index


def serialize_parameters(metadata_dict: Dict[id, ParameterMetadata], parameter_value):
    serialize_buffer = io.BytesIO()  # inner_encoder updates the serialize_buffer
    for i, parameter in enumerate(parameter_value):
        encoder = serializationstrategy.Context.get_encoder(
            metadata_dict[i + 1].type,
            metadata_dict[i + 1].repeated,
        )
        inner_encoder = encoder(i + 1)
        inner_encoder(serialize_buffer.write, parameter, None)
    return serialize_buffer.getvalue()

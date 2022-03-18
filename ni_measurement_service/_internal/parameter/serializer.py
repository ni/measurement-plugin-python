"""Parameter Serializer."""
import io
from typing import Dict

import ni_measurement_service._internal.parameter.serializationstrategy as serializationstrategy
from google.protobuf.internal import encoder
from ni_measurement_service._internal.parameter.metadata import ParameterMetadata


def deserialize_parameters(metadata_dict: Dict[id, ParameterMetadata], parameter_bytes):
    """To do.

    Args
    ----
        metadata_dict (Dict[id, ParameterMetadata]): _description_
        parameter_bytes (_type_): _description_

    Returns
    -------
        _type_: _description_

    """
    # Getting overlapping parameters
    overlapping_field_indices = list()
    mapping_by_filed_index = _get_overlapping_parameters(metadata_dict, parameter_bytes, overlapping_field_indices)
    # Adding missing parameters with type defaults
    missing_parameters = _get_missing_parameters(metadata_dict, overlapping_field_indices)
    mapping_by_filed_index.update(missing_parameters)
    return mapping_by_filed_index


def serialize_parameters(metadata_dict: Dict[id, ParameterMetadata], parameter_value):
    """Todo.

    Args
    ----
        metadata_dict (Dict[id, ParameterMetadata]): _description_
        parameter_value (_type_): _description_

    Returns
    -------
        _type_: _description_

    """
    serialize_buffer = io.BytesIO()  # inner_encoder updates the serialize_buffer
    for i, parameter in enumerate(parameter_value):
        encoder = serializationstrategy.Context.get_encoder(
            metadata_dict[i + 1].type,
            metadata_dict[i + 1].repeated,
        )
        type_default_value = serializationstrategy.Context.get_type_default(
            metadata_dict[i + 1].type,
            metadata_dict[i + 1].repeated,
        )
        # Skipping serialization if the value is None or if its a type default value.
        if parameter is None or parameter == type_default_value:
            continue
        inner_encoder = encoder(i + 1)
        inner_encoder(serialize_buffer.write, parameter, None)
    return serialize_buffer.getvalue()


def serialize_default_values(metadata_dict: Dict[id, ParameterMetadata]):
    default_value_parameter_array = list()
    for parameter in metadata_dict.values():
        parameter: ParameterMetadata
        default_value = parameter.default_value
        default_value_parameter_array.append(default_value)
    return serialize_parameters(metadata_dict, default_value_parameter_array)


def _get_current_field_index(parameter_bytes, position):
    return parameter_bytes[position] >> 3


def _get_overlapping_parameters(parameter_metadata_dict: Dict[id, ParameterMetadata], parameter_bytes, overlapping_field_indices):
    """
    Gets the parameters present in both `parameter_metadata_dict` and `parameter_bytes`
    """
    overlapping_parameters = {}  # inner_decoder update the overlapping_parameters
    position = 0
    while position < len(parameter_bytes):
        field_index = _get_current_field_index(parameter_bytes, position)
        if field_index not in parameter_metadata_dict:
            raise Exception(f"Error occurred while reading the parameter - given protobuf index '{field_index}' is invalid.")
        overlapping_field_indices.append(field_index)
        name = parameter_metadata_dict[field_index].name
        type = parameter_metadata_dict[field_index].type
        is_repeated = parameter_metadata_dict[field_index].repeated
        decoder = serializationstrategy.Context.get_decoder(type, is_repeated)
        inner_decoder = decoder(field_index, name)
        position = inner_decoder(
            parameter_bytes,
            position + encoder._TagSize(field_index),
            len(parameter_bytes),
            type,
            overlapping_parameters,
        )
    return overlapping_parameters


def _get_missing_parameters(parameter_metadata_dict: Dict[id, ParameterMetadata], overlapping_field_indices):
    """
    Get the Parameters whose field indices are defined in `parameter_metadata_dict` but not available in `overlapping_field_indices`
    """
    missing_parameters = {}
    for key, value in parameter_metadata_dict.items():
        if key not in overlapping_field_indices:
            missing_parameters[value.name] = serializationstrategy.Context.get_type_default(value.type, value.repeated)
    return missing_parameters

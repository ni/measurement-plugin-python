"""Parameter Serializer."""

from typing import Any, Dict, cast

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.internal.decoder import (  # type: ignore[attr-defined]
    _DecodeSignedVarint32,
)
from google.protobuf.message import Message

from ni_measurement_plugin_sdk_service._internal.parameter import decoder_strategy
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
    get_enum_values_annotation,
)

_GRPC_WIRE_TYPE_BIT_WIDTH = 3


def deserialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_bytes: bytes
) -> Dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

    Returns:
        Dict[int, Any]: Deserialized parameters by ID
    """
    # Getting overlapping parameters
    overlapping_parameter_by_id = _get_overlapping_parameters(
        parameter_metadata_dict, parameter_bytes
    )

    # Deserialization enum parameters to their user-defined type
    _deserialize_enum_parameters(parameter_metadata_dict, overlapping_parameter_by_id)

    # Adding missing parameters with type defaults
    missing_parameters = _get_missing_parameters(
        parameter_metadata_dict, overlapping_parameter_by_id
    )
    overlapping_parameter_by_id.update(missing_parameters)
    return overlapping_parameter_by_id


def _get_overlapping_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_bytes: bytes
) -> Dict[int, Any]:
    """Get the parameters present in both `parameter_metadata_dict` and `parameter_bytes`.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): bytes of Parameter that need to be deserialized.

    Raises:
        Exception: If the protobuf filed index is invalid.

    Returns:
        Dict[int, Any]: Overlapping Parameters by ID.
    """
    # inner_decoder update the overlapping_parameters
    overlapping_parameters_by_id: Dict[int, Any] = {}
    position = 0
    parameter_bytes_memory_view = memoryview(parameter_bytes)
    while position < len(parameter_bytes):
        (tag, position) = _DecodeSignedVarint32(parameter_bytes_memory_view, position)
        field_index = tag >> _GRPC_WIRE_TYPE_BIT_WIDTH
        if field_index not in parameter_metadata_dict:
            raise Exception(
                f"Error occurred while reading the parameter - given protobuf index '{field_index}' is invalid."
            )
        field_metadata = parameter_metadata_dict[field_index]
        decoder = decoder_strategy.get_decoder(
            field_metadata.type, field_metadata.repeated, field_metadata.message_type
        )
        inner_decoder = decoder(field_index, cast(FieldDescriptor, field_index))
        position = inner_decoder(
            parameter_bytes_memory_view,
            position,
            len(parameter_bytes),
            cast(Message, None),  # unused - See serialization_strategy._vector_decoder._new_default
            cast(Dict[FieldDescriptor, Any], overlapping_parameters_by_id),
        )
    return overlapping_parameters_by_id


def _get_missing_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_by_id: Dict[int, Any]
) -> Dict[int, Any]:
    """Get the Parameters defined in `parameter_metadata_dict` but not in `parameter_by_id`.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by id.

        parameter_by_id (Dict[int, Any]): Parameters by ID to compare the metadata with.

    Returns:
        Dict[int, Any]: Missing parameter(as type defaults) by ID.
    """
    missing_parameters = {}
    for key, value in parameter_metadata_dict.items():
        if key not in parameter_by_id:
            enum_annotations = get_enum_values_annotation(value)
            if enum_annotations and not value.repeated:
                enum_type = _get_enum_type(value)
                missing_parameters[key] = enum_type(0)
            else:
                missing_parameters[key] = decoder_strategy.get_type_default(
                    value.type, value.repeated
                )
    return missing_parameters


def _deserialize_enum_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_by_id: Dict[int, Any]
) -> None:
    """Converts all enums in `parameter_by_id` to the user defined enum type.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by id.

        parameter_by_id (Dict[int, Any]): Parameters by ID to compare the metadata with.
    """
    for id, value in parameter_by_id.items():
        parameter_metadata = parameter_metadata_dict[id]
        if get_enum_values_annotation(parameter_metadata):
            enum_type = _get_enum_type(parameter_metadata)
            is_protobuf_enum = enum_type is int
            if parameter_metadata.repeated:
                for index, member_value in enumerate(value):
                    if is_protobuf_enum:
                        parameter_by_id[id][index] = member_value
                    else:
                        parameter_by_id[id][index] = enum_type(member_value)
            else:
                if is_protobuf_enum:
                    parameter_by_id[id] = value
                else:
                    parameter_by_id[id] = enum_type(value)


def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        return type(parameter_metadata.default_value[0])
    else:
        return type(parameter_metadata.default_value)

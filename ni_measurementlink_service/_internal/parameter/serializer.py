"""Parameter Serializer."""

from enum import Enum
from io import BytesIO
from typing import Any, Dict, Sequence, cast

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.internal.decoder import (  # type: ignore[attr-defined]
    _DecodeSignedVarint32,
)
from google.protobuf.message import Message

from ni_measurementlink_service._annotations import (
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurementlink_service._internal.parameter import serialization_strategy
from ni_measurementlink_service._internal.parameter.metadata import (
    ParameterMetadata,
    get_enum_values_annotation,
)
from ni_measurementlink_service.measurement.info import TypeSpecialization

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


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_value (Sequence[Any]): Parameter values to serialize.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    serialize_buffer = BytesIO()  # inner_encoder updates the serialize_buffer
    for i, parameter in enumerate(parameter_values):
        parameter_metadata = parameter_metadata_dict[i + 1]
        encoder = serialization_strategy.get_encoder(
            parameter_metadata.type,
            parameter_metadata.repeated,
        )
        type_default_value = serialization_strategy.get_type_default(
            parameter_metadata.type,
            parameter_metadata.repeated,
        )
        # Convert enum parameters to their underlying value if necessary.
        if (
            parameter_metadata.annotations.get(TYPE_SPECIALIZATION_KEY)
            == TypeSpecialization.Enum.value
        ):
            parameter = _get_enum_value(parameter, parameter_metadata.repeated)
        # Skipping serialization if the value is None or if its a type default value.
        if parameter is not None and parameter != type_default_value:
            inner_encoder = encoder(i + 1)
            inner_encoder(serialize_buffer.write, parameter, False)
    return serialize_buffer.getvalue()


def serialize_default_values(parameter_metadata_dict: Dict[int, ParameterMetadata]) -> bytes:
    """Serialize the Default values in the Metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Configuration metadata.

    Returns:
        bytes: Serialized byte string containing default values.
    """
    default_value_parameter_array = list()
    default_value_parameter_array = [
        parameter.default_value for parameter in parameter_metadata_dict.values()
    ]
    return serialize_parameters(parameter_metadata_dict, default_value_parameter_array)


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
        decoder = serialization_strategy.get_decoder(
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
                missing_parameters[key] = serialization_strategy.get_type_default(
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


def _get_enum_value(parameter: Any, repeated: bool) -> Any:
    if repeated:
        if len(parameter) > 0 and isinstance(parameter[0], Enum):
            return [x.value for x in parameter]
    else:
        if isinstance(parameter, Enum):
            return parameter.value
    return parameter


def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        return type(parameter_metadata.default_value[0])
    else:
        return type(parameter_metadata.default_value)

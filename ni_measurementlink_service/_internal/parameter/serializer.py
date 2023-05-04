"""Parameter Serializer."""

from io import BytesIO
from typing import Any, Dict, Sequence

from google.protobuf.internal import encoder

from ni_measurementlink_service._internal.parameter import serialization_strategy
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata

_GRPC_WIRE_TYPE_BIT_WIDTH = 3


def deserialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_bytes: bytes
) -> Dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args
    ----
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

    Returns
    -------
        Dict[int, Any]: Deserialized parameters by ID

    """
    # Getting overlapping parameters
    overlapping_parameter_by_id = _get_overlapping_parameters(
        parameter_metadata_dict, parameter_bytes
    )
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

    Args
    ----
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_value (Sequence[Any]): Parameter values to serialize.

    Returns
    -------
        bytes: Serialized byte string containing parameter values.

    """
    serialize_buffer = BytesIO()  # inner_encoder updates the serialize_buffer
    for i, parameter in enumerate(parameter_values):
        parameter_metadata = parameter_metadata_dict[i + 1]
        encoder = serialization_strategy.Context.get_encoder(
            parameter_metadata.type,
            parameter_metadata.repeated,
        )
        type_default_value = serialization_strategy.Context.get_type_default(
            parameter_metadata.type,
            parameter_metadata.repeated,
        )
        # Skipping serialization if the value is None or if its a type default value.
        if parameter is not None and parameter != type_default_value:
            inner_encoder = encoder(i + 1)
            inner_encoder(serialize_buffer.write, parameter, None)
    return serialize_buffer.getvalue()


def serialize_default_values(parameter_metadata_dict: Dict[int, ParameterMetadata]) -> bytes:
    """Serialize the Default values in the Metadata.

    Args
    -----
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Configuration metadata.

    Returns
    -------
        bytes: Serialized byte string containing default values.

    """
    default_value_parameter_array = list()
    default_value_parameter_array = [
        parameter.default_value for parameter in parameter_metadata_dict.values()
    ]
    return serialize_parameters(parameter_metadata_dict, default_value_parameter_array)


def _get_field_index(parameter_bytes: bytes, tag_position: int):
    """Get the Filed Index based on the tag's position.

    The tag Position should be the index of the TagValue in the ByteArray for valid field index.

    Args
    ----
        parameter_bytes (bytes): Serialized bytes

        tag_position (int): Tag position

    Returns
    -------
        int: Filed index of the Tag Position

    """
    return parameter_bytes[tag_position] >> _GRPC_WIRE_TYPE_BIT_WIDTH


def _get_overlapping_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_bytes: bytes
) -> Dict[int, Any]:
    """Get the parameters present in both `parameter_metadata_dict` and `parameter_bytes`.

    Args
    ----
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): bytes of Parameter that need to be deserialized.

    Raises
    ------
        Exception: If the protobuf filed index is invalid.

    Returns
    -------
        Dict[int, Any]: Overlapping Parameters by ID.

    """
    # inner_decoder update the overlapping_parameters
    overlapping_parameters_by_id: Dict[int, Any] = {}
    position = 0
    while position < len(parameter_bytes):
        field_index = _get_field_index(parameter_bytes, position)
        if field_index not in parameter_metadata_dict:
            raise Exception(
                f"Error occurred while reading the parameter - given protobuf index '{field_index}' is invalid."
            )
        type = parameter_metadata_dict[field_index].type
        is_repeated = parameter_metadata_dict[field_index].repeated
        decoder = serialization_strategy.Context.get_decoder(type, is_repeated)
        inner_decoder = decoder(field_index, field_index)
        parameter_bytes_io = BytesIO(parameter_bytes)
        parameter_bytes_memory_view = parameter_bytes_io.getbuffer()
        position = inner_decoder(
            parameter_bytes_memory_view,
            position + encoder._TagSize(field_index),  # type: ignore[attr-defined]
            len(parameter_bytes),
            type,
            overlapping_parameters_by_id,
        )
    return overlapping_parameters_by_id


def _get_missing_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_by_id: Dict[int, Any]
) -> Dict[int, Any]:
    """Get the Parameters defined in `parameter_metadata_dict` but not in `parameter_by_id`.

    Args
    ----
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by id.

        parameter_by_id (Dict[int, Any]): Parameters by ID to compare the metadata with.

    Returns
    -------
        Dict[int, Any]: Missing parameter(as type defaults) by ID.

    """
    missing_parameters = {}
    for key, value in parameter_metadata_dict.items():
        if key not in parameter_by_id:
            missing_parameters[key] = serialization_strategy.Context.get_type_default(
                value.type, value.repeated
            )
    return missing_parameters

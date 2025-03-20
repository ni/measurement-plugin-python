"""Support functions for the Measurement Plug-In Client."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._annotations import TYPE_SPECIALIZATION_KEY
from ni_measurement_plugin_sdk_service._internal.parameter.decoder import (
    deserialize_parameters as _internal_deserialize_parameters,
)
from ni_measurement_plugin_sdk_service._internal.parameter.encoder import (
    serialize_parameters as _internal_serialize_parameters,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    create_file_descriptor,
)
from ni_measurement_plugin_sdk_service.measurement.info import TypeSpecialization

__all__ = [
    "create_file_descriptor",
    "deserialize_parameters",
    "ParameterMetadata",
    "serialize_parameters",
]


def deserialize_parameters(
    parameter_metadata_dict: dict[int, ParameterMetadata],
    parameter_bytes: bytes,
    message_name: str,
    *,
    convert_paths: bool = True,
) -> Sequence[Any]:
    """Deserialize parameter bytes into separate parameter values.

    Args:
        parameter_metadata_dict: Parameter metadata by ID.

        parameter_byte: Byte string to deserialize.

        message_name: gRPC message name (e.g. f"{service_class}.Outputs").

        convert_paths: Specifies whether to convert path parameters to pathlib.Path.

    Returns:
        Deserialized parameter values, ordered by ID.
    """
    parameter_values = _internal_deserialize_parameters(
        parameter_metadata_dict, parameter_bytes, message_name
    )

    for id in parameter_values.keys():
        metadata = parameter_metadata_dict[id]
        if (
            convert_paths
            and metadata.type == FieldDescriptorProto.TYPE_STRING
            and metadata.annotations
            and metadata.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.Path.value
        ):
            if metadata.repeated:
                parameter_values[id] = [Path(value) for value in parameter_values[id]]
            else:
                parameter_values[id] = Path(parameter_values[id])

    if parameter_metadata_dict:
        result = [None] * max(parameter_metadata_dict.keys())
    else:
        result = []

    for k, v in parameter_values.items():
        result[k - 1] = v

    return result


def serialize_parameters(
    parameter_metadata_dict: dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
    message_name: str,
) -> bytes:
    """Serialize parameter values into a parameter byte string.

    Args:
        parameter_metadata_dict: Parameter metadata by ID.

        parameter_values: Parameter values to serialize, ordered by ID.

        message_name: gRPC message name (e.g. f"{service_class}.Configurations").

    Returns:
        Serialized byte string containing parameter values.
    """
    new_parameter_values = list(parameter_values)

    for id in parameter_metadata_dict.keys():
        index = id - 1
        metadata = parameter_metadata_dict[id]
        if (
            metadata.type == FieldDescriptorProto.TYPE_STRING
            and metadata.annotations
            and metadata.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.Path.value
        ):
            if metadata.repeated:
                new_parameter_values[index] = [str(value) for value in parameter_values[index]]
            else:
                new_parameter_values[index] = str(parameter_values[index])

    return _internal_serialize_parameters(
        parameter_metadata_dict, new_parameter_values, message_name
    )

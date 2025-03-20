"""Parameter Serializer."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter._get_type import (
    get_type_default,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)


def serialize_parameters(
    parameter_metadata_dict: dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
    service_name: str,
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_values (Sequence[Any]): Parameter values to serialize.

        service_name (str): Unique service name.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    pool = descriptor_pool.Default()
    message_proto = pool.FindMessageTypeByName(service_name)
    message_instance = message_factory.GetMessageClass(message_proto)()

    for i, parameter in enumerate(parameter_values, start=1):
        parameter_metadata = parameter_metadata_dict[i]
        field_name = parameter_metadata.field_name
        parameter = _get_enum_values(param=parameter)
        default_value = get_type_default(parameter_metadata.type, parameter_metadata.repeated)

        # Doesn't assign default values or None values to fields
        if parameter != default_value and parameter is not None:
            if parameter_metadata.repeated:
                getattr(message_instance, field_name).extend(parameter)
            elif parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
                getattr(message_instance, field_name).CopyFrom(parameter)
            else:
                setattr(message_instance, field_name, parameter)
    return message_instance.SerializeToString()


def serialize_default_values(
    parameter_metadata_dict: dict[int, ParameterMetadata], service_name: str
) -> bytes:
    """Serialize the Default values in the Metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Configuration metadata.

        service_name (str): Unique service name.

    Returns:
        bytes: Serialized byte string containing default values.
    """
    default_value_parameter_array = [
        parameter.default_value for parameter in parameter_metadata_dict.values()
    ]
    return serialize_parameters(
        parameter_metadata_dict, default_value_parameter_array, service_name
    )


def _get_enum_values(param: Any) -> Any:
    """Get's value of an enum."""
    if param == []:
        return param
    if isinstance(param, list) and isinstance(param[0], Enum):
        return [x.value for x in param]
    elif isinstance(param, Enum):
        return param.value
    return param

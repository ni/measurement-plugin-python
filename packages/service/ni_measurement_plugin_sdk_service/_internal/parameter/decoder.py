from __future__ import annotations

"""Parameter Serializer."""

from typing import Any

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    is_protobuf,
)


def deserialize_parameters(
    parameter_metadata_dict: dict[int, ParameterMetadata],
    parameter_bytes: bytes,
    service_name: str,
) -> dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

        service_name (str): Unique service name.

    Returns:
        Dict[int, Any]: Deserialized parameters by ID.
    """
    pool = descriptor_pool.Default()
    message_proto = pool.FindMessageTypeByName(service_name)
    message_instance = message_factory.GetMessageClass(message_proto)()
    parameter_values = {}

    message_instance.ParseFromString(parameter_bytes)
    for i in message_proto.fields_by_number.keys():
        parameter_metadata = parameter_metadata_dict[i]
        field_name = parameter_metadata.field_name
        value = getattr(message_instance, field_name)

        if parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM:
            parameter_values[i] = _deserialize_enum_parameter(value, parameter_metadata)
        elif (
            parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE
            and not parameter_metadata.repeated
            and value.ByteSize() == 0
        ):
            parameter_values[i] = None
        else:
            parameter_values[i] = value
    return parameter_values


def _deserialize_enum_parameter(field_value: Any, metadata: ParameterMetadata) -> Any:
    """Convert enum into their user defined enum type."""
    enum_type = metadata.enum_type
    if is_protobuf(enum_type):
        return field_value

    assert enum_type is not None
    if metadata.repeated:
        return [enum_type(value) for value in field_value]
    return enum_type(field_value)

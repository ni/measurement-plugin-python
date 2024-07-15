"""Parameter Serializer."""

from json import loads
from typing import Any, Dict

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    _get_enum_type,
)


def deserialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_bytes: bytes,
    service_name: str,
) -> Dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

        service_name (str): Unique service name.

    Returns:
        Dict[int, Any]: Deserialized parameters by ID
    """
    pool = descriptor_pool.Default()
    message_proto = pool.FindMessageTypeByName(service_name)
    message_instance = message_factory.GetMessageClass(message_proto)()
    parameter_values = {}

    message_instance.ParseFromString(parameter_bytes)
    for i in message_proto.fields_by_number.keys():
        parameter_metadata = parameter_metadata_dict[i]
        field_name = parameter_metadata.sanitized_display_name()
        value = getattr(message_instance, field_name)

        if (
            parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM
            and _get_enum_type(parameter_metadata) is not int
        ):
            parameter_values[i] = _deserialize_enum_parameter(parameter_metadata, value)
        elif (
            parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE
            and not parameter_metadata.repeated
            and value.ByteSize() == 0
        ):
            parameter_values[i] = None
        else:
            parameter_values[i] = value
    return parameter_values


def _deserialize_enum_parameter(parameter_metadata: ParameterMetadata, field_value: Any) -> Any:
    """Convert all enums into the user defined enum type.

    Args:
        parameter_metadata (ParameterMetadata): Metadata of current enum value.

        field_value (Any): Value of current field.

    Returns:
        Any: Enum type or a list of enum types.
    """
    enum_dict = loads(parameter_metadata.annotations[ENUM_VALUES_KEY])
    enum_type = _get_enum_type(parameter_metadata)
    if parameter_metadata.repeated:
        return [_get_enum_field(enum_dict, enum_type, value) for value in field_value]
    else:
        return _get_enum_field(enum_dict, enum_type, field_value)


def _get_enum_field(enum_dict: Dict[Any, int], enum_type: Any, field_value: int) -> Any:
    """Get enum type and value from 'field_value'.

    Args:
        enum_dict (Dict[Any, int]): List enum class of 'field_value'.

        enum_type (Any): 'field_value' enum class name.

        field_value (int): Default value of current field.

    Returns:
        Any: Enum type of 'field_value' from 'enum_dict' with the enum value.
    """
    for name in enum_dict.keys():
        enum_value = getattr(enum_type, name)
        if field_value == enum_value.value:
            return enum_value

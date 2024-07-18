"""Parameter Serializer."""

from typing import Any, Dict, List, Union

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

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
        enum_type = _get_enum_type(parameter_metadata)
        value = getattr(message_instance, field_name)

        if parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM and enum_type is not int:
            parameter_values[i] = _deserialize_enum_parameter(
                parameter_metadata.repeated, value, enum_type
            )
        elif (
            parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE
            and not parameter_metadata.repeated
            and value.ByteSize() == 0
        ):
            parameter_values[i] = None
        else:
            parameter_values[i] = value
    return parameter_values


def _deserialize_enum_parameter(
    repeated: bool, field_value: Any, enum_type: Any
) -> Union[List[Any], Any]:
    """Convert all enums into the user defined enum type.

    Returns:
        Union[List[Any], Any]: Enum type or a list of enum types.
    """
    if repeated:
        return [enum_type(value) for value in field_value]
    return enum_type(field_value)

"""Parameter Serializer."""

from typing import Any, Dict

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_strategy import (
    _get_enum_type,
    create_message_type,
    deserialize_enum_parameter,
)
from ni_measurement_plugin_sdk_service.measurement.info import ServiceInfo


def deserialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_bytes: bytes,
    service_info: ServiceInfo,
) -> Dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

        Service_info (ServiceInfo): Unique service name.

    Returns:
        Dict[int, Any]: Deserialized parameters by ID
    """
    pool = descriptor_pool.Default()
    service_name = "".join(char for char in service_info.service_class if char.isalpha())
    message_name = service_name + "DESERIALIZE"
    try:
        message_proto = pool.FindMessageTypeByName(f"{message_name}.{message_name}")
    except KeyError:
        message_proto = create_message_type(parameter_metadata_dict, message_name, pool)
    message_instance = message_factory.GetMessageClass(message_proto)()

    parameter_values = {}
    message_instance.ParseFromString(parameter_bytes)
    for i in message_proto.fields_by_number.keys():
        field_name = f"field_{i}"
        parameter_metadata = parameter_metadata_dict[i]
        value = getattr(message_instance, field_name)

        if (
            parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM
            and _get_enum_type(parameter_metadata) is not int
        ):
            parameter_values[i] = deserialize_enum_parameter(
                parameter_metadata, message_instance, field_name
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

"""Parameter Serializer."""

from typing import Any, Dict, Sequence

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter.default_value import (
    get_type_default,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_strategy import (
    create_message_type,
    get_enum_values,
)
from ni_measurement_plugin_sdk_service.measurement.info import ServiceInfo


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
    service_info: ServiceInfo,
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_values (Sequence[Any]): Parameter values to serialize.

        Service_info (ServiceInfo): Unique service name.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    pool = descriptor_pool.Default()
    service_name = "".join(char for char in service_info.service_class if char.isalpha())
    message_name = service_name + "SERIALIZE"
    # Tries to find a message type in pool with message_name else it creates one
    try:
        message_proto = pool.FindMessageTypeByName(f"{message_name}.{message_name}")
    except KeyError:
        message_proto = create_message_type(parameter_metadata_dict, message_name, pool)
    message_instance = message_factory.GetMessageClass(message_proto)()

    for i, parameter in enumerate(parameter_values, start=1):
        field_name = f"field_{i}"
        parameter_metadata = parameter_metadata_dict[i]
        parameter = get_enum_values(param=parameter)
        type_default_value = get_type_default(parameter_metadata.type, parameter_metadata.repeated)

        # Doesn't assign default values or None values to fields
        if parameter != type_default_value and parameter is not None:
            if parameter_metadata.repeated:
                getattr(message_instance, field_name).extend(parameter)
            elif parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
                getattr(message_instance, field_name).CopyFrom(parameter)
            else:
                setattr(message_instance, field_name, parameter)
    return message_instance.SerializeToString()


def serialize_default_values(
    parameter_metadata_dict: Dict[int, ParameterMetadata], service_info: ServiceInfo
) -> bytes:
    """Serialize the Default values in the Metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Configuration metadata.

        Service_info (ServiceInfo): Unique service name.

    Returns:
        bytes: Serialized byte string containing default values.
    """
    default_value_parameter_array = [
        parameter.default_value for parameter in parameter_metadata_dict.values()
    ]
    return serialize_parameters(
        parameter_metadata_dict, default_value_parameter_array, service_info
    )

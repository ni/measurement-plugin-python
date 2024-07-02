# enums and default values
from enum import Enum
from typing import Any, Dict, Sequence

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter.decoder_strategy import (
    get_type_default,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service.measurement.info import ServiceInfo
from tests.utilities.stubs.loopback.types_pb2 import ProtobufColor


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
    service_info: ServiceInfo,
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_value (Sequence[Any]): Parameter values to serialize.

        Service_info (ServiceInfo): Unique service name.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    pool = descriptor_pool.Default()
    message_name = "".join(char for char in service_info.service_class if char.isalpha())
    # Tries to find a message type in pool with message_name else it creates one
    try:
        message_proto = pool.FindMessageTypeByName(f"{message_name}.{message_name}")
    except KeyError:
        message_proto = _create_message_type(
            parameter_values, parameter_metadata_dict, message_name, pool
        )
    message_instance = message_factory.GetMessageClass(message_proto)()

    for i, parameter in enumerate(parameter_values, start=1):
        field_name = f"field_{i}"
        parameter_metadata = parameter_metadata_dict[i]
        parameter = _get_enum_values(param=parameter)
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


def _create_message_type(
    parameter_values: Sequence[Any],
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    message_name: str,
    pool: descriptor_pool.DescriptorPool,
) -> Any:
    """Creates a message descriptor with the fields defined in a file descriptor proto.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_value (Sequence[Any]): Parameter values to serialize.

        message_name (str): Service class name.

        pool (descriptor_pool.DescriptorPool): Descriptor pool holding file descriptors.

    Returns:
        Any: A message descriptor based on a defined message_descriptor
    """
    file_descriptor = descriptor_pb2.FileDescriptorProto()
    file_descriptor.name = message_name
    file_descriptor.package = message_name
    message_proto = file_descriptor.message_type.add()
    message_proto.name = message_name

    # Initialize the message with fields defined
    for i, parameter in enumerate(parameter_values, start=1):
        parameter_metadata = parameter_metadata_dict[i]
        field_descriptor = _create_field(
            message_proto=message_proto, metadata=parameter_metadata, index=i
        )
        if parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM:
            _create_enum_type(
                file_descriptor=file_descriptor,
                param=parameter,
                field_descriptor=field_descriptor,
            )
    pool.Add(file_descriptor)
    return pool.FindMessageTypeByName(f"{file_descriptor.package}.{message_proto.name}")


def _get_enum_values(param: Any) -> Any:
    """Get's value of an enum.

    Args:
        param (Any): A value/parameter of parameter_values.

    Returns:
        Any: An enum value or a list of enums or the 'param'.
    """
    if param == []:
        return param
    if isinstance(param, list) and isinstance(param[0], Enum):
        return [x.value for x in param]
    elif isinstance(param, Enum):
        return param.value
    return param


def _create_enum_type(
    file_descriptor: descriptor_pb2.FileDescriptorProto,
    param: Any,
    field_descriptor: FieldDescriptorProto,
) -> None:
    """Implement a enum class in 'file_descriptor'.

    Args:
        file_descriptor (FileDescriptorProto): Descriptor of a proto file.

        param (Any): A value/parameter of parameter_values.

        field_descriptor (FieldDescriptorProto): Descriptor of a field.
    """
    if isinstance(param, list):
        param = param[0]
    # if there are no enums/param is a different enum and is a python enum, defines a enum field
    if param.__class__.__name__ not in [
        enum.name for enum in file_descriptor.enum_type
    ] and isinstance(param, Enum):
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = param.__class__.__name__

        for name, number in param.__class__.__members__.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = name
            enum_value_descriptor.number = number.value
    # checks enum if it's protobuf or python
    try:
        field_descriptor.type_name = ProtobufColor.DESCRIPTOR.full_name
    except TypeError:
        field_descriptor.type_name = param.__class__.__name__


def _create_field(
    message_proto: Any, metadata: ParameterMetadata, index: int
) -> FieldDescriptorProto:
    """Implement a field in 'message_proto'.

    Args:
        message_proto (message_type): A message instance in '_FILE_DESCRIPTOR_PROTO'.

        metadata (ParameterMetadata): Metadata of 'param'.

        index (int): 'param' index in parameter_values

    Returns:
        Any: field_descriptor of 'param'.
    """
    field_descriptor = message_proto.field.add()
    field_descriptor.number = index
    field_descriptor.name = f"field_{index}"
    field_descriptor.type = metadata.type

    if metadata.repeated:
        field_descriptor.label = FieldDescriptorProto.LABEL_REPEATED
        field_descriptor.options.packed = True
    else:
        field_descriptor.label = FieldDescriptorProto.LABEL_OPTIONAL

    if metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
        field_descriptor.type_name = metadata.message_type
    return field_descriptor

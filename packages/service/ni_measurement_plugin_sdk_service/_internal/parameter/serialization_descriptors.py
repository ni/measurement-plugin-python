"""Serialization Descriptors."""

from json import loads
from typing import Any, List

from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from tests.utilities.stubs.loopback.types_pb2 import ProtobufColor


def _get_output_enum_type(
    metadata_enum_list: List[str],
    file_descriptor: descriptor_pb2.FileDescriptorProto,
) -> Any:
    """Get's matching enum class from 'file_descriptor'.

    Args:
        metadata_enum_list (List[str]): Enum names from metadata.annotations.

        file_descriptor: Descriptor of proto file.

    Returns:
        Any: Matching enum class in a str type or None when enum is protobuf.
    """
    for enum_type in file_descriptor.enum_type:
        enum_names = [enum_value.name for enum_value in enum_type.value]
        if sorted(metadata_enum_list) == sorted(enum_names):
            return enum_type.name
    return None


def _create_enum_type(
    file_descriptor: descriptor_pb2.FileDescriptorProto,
    parameter_metadata: ParameterMetadata,
    field_descriptor: FieldDescriptorProto,
) -> None:
    """Implement a enum class in 'file_descriptor'.

    Args:
        file_descriptor (FileDescriptorProto): Descriptor of a proto file.

        parmeter_metadata (ParameterMetadata): Metadata of current field.

        field_descriptor (FieldDescriptorProto): Descriptor of a field.

    Returns:
        None: Only creates a enum class in file_descriptor.
    """
    enum_dict = loads(parameter_metadata.annotations[ENUM_VALUES_KEY])
    if parameter_metadata.default_value is None:
        enum_type_name = _get_output_enum_type(
            metadata_enum_list=[enum for enum in enum_dict.keys()], file_descriptor=file_descriptor
        )
    else:
        enum_type_name = _get_enum_type(parameter_metadata).__name__

    if enum_type_name == "int" or enum_type_name is None:
        field_descriptor.type_name = ProtobufColor.DESCRIPTOR.full_name
    elif enum_type_name not in [enum_type.name for enum_type in file_descriptor.enum_type]:
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = enum_type_name
        for name, number in enum_dict.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = name
            enum_value_descriptor.number = number
        field_descriptor.type_name = enum_descriptor.name
    else:
        field_descriptor.type_name = enum_type_name


def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        return type(parameter_metadata.default_value[0])
    else:
        return type(parameter_metadata.default_value)


def _create_field(
    message_proto: Any, metadata: ParameterMetadata, index: int
) -> FieldDescriptorProto:
    """Implement a field in 'message_proto'.

    Args:
        message_proto (message_type): A message instance in a file descriptor proto.

        metadata (ParameterMetadata): Metadata of 'param'.

        index (int): 'param' index in parameter_values

    Returns:
        FieldDescriptorProto: field_descriptor of 'param'.
    """
    field_descriptor = message_proto.field.add()
    field_descriptor.number = index
    field_descriptor.name = metadata.sanitized_display_name()
    field_descriptor.type = metadata.type

    if metadata.repeated:
        field_descriptor.label = FieldDescriptorProto.LABEL_REPEATED
        field_descriptor.options.packed = True
    else:
        field_descriptor.label = FieldDescriptorProto.LABEL_OPTIONAL

    if metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
        field_descriptor.type_name = metadata.message_type
    return field_descriptor


def create_file_descriptor(
    service_name: str,
    output_metadata: List[ParameterMetadata],
    input_metadata: List[ParameterMetadata],
    pool: descriptor_pool.DescriptorPool,
) -> None:
    """Creates two message types in one file descriptor proto.

    Args:
        service_class_name (str): Unique service name.

        output_metadata (List[ParameterMetadata]): Metadata of output parameters.

        input_metadata (List[ParameterMetadata]): Metadata of input parameters.

        pool (DescriptorPool): Descriptor pool holding file descriptors and enum classes.

    Returns:
        None: Only creates a file and two message descriptors.
    """
    service_name = "".join(char for char in service_name if char.isalpha())
    try:
        pool.FindFileByName(service_name)
    except KeyError:
        file_descriptor = descriptor_pb2.FileDescriptorProto()
        file_descriptor.name = service_name
        file_descriptor.package = service_name

        _create_message_type(input_metadata, "Inputs", file_descriptor)
        _create_message_type(output_metadata, "Outputs", file_descriptor)
        pool.Add(file_descriptor)


def _create_message_type(
    parameter_metadata: List[ParameterMetadata],
    message_name: str,
    file_descriptor: descriptor_pb2.FileDescriptorProto,
) -> None:
    """Creates a message descriptor with the fields defined in a file descriptor proto.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        message_name (str): Service class name.

        file_descriptor (descriptor_pb2.FileDescriptorProto): Descriptor of a proto file.

    Returns:
        None: Only creates a message_type in 'file_descriptor'.
    """
    message_proto = file_descriptor.message_type.add()
    message_proto.name = message_name

    # Initialize the message with fields defined
    for i, metadata in enumerate(parameter_metadata):
        field_descriptor = _create_field(
            message_proto=message_proto, metadata=metadata, index=i + 1
        )
        if metadata.type == FieldDescriptorProto.TYPE_ENUM:
            _create_enum_type(
                file_descriptor=file_descriptor,
                parameter_metadata=metadata,
                field_descriptor=field_descriptor,
            )

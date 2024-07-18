"""Serialization Descriptors."""

from json import loads
from typing import List

from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto, DescriptorProto

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)


def _create_enum_type_class(
    file_descriptor: descriptor_pb2.FileDescriptorProto,
    parameter_metadata: ParameterMetadata,
    field_descriptor: FieldDescriptorProto,
) -> None:
    """Implement a enum class in 'file_descriptor'."""
    enum_dict = loads(parameter_metadata.annotations[ENUM_VALUES_KEY])
    enum_type_name = _get_enum_type(parameter_metadata).__name__
    
    # if enum is a protobuf then enum_type_name is 1st letter of each enum name
    # e.g. {"NONE": 0, "RED": 1, "GREEN": 2} -> NRG
    if enum_type_name == "int" or enum_type_name == "NoneType":
        enum_field_names = list(enum_dict.keys())[:]
        enum_type_name = "".join(name[0] for name in enum_field_names)

    if enum_type_name not in [enum_type.name for enum_type in file_descriptor.enum_type]:
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = enum_type_name
        for name, number in enum_dict.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = f"{enum_type_name}_{name}"
            enum_value_descriptor.number = number
    field_descriptor.type_name = enum_type_name


def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        return type(parameter_metadata.default_value[0])
    else:
        return type(parameter_metadata.default_value)


def _create_field(
    message_proto: DescriptorProto, metadata: ParameterMetadata, index: int
) -> FieldDescriptorProto:
    """Implement a field in 'message_proto'."""
    field_descriptor = message_proto.field.add()
    field_descriptor.number = index
    field_descriptor.name = metadata.field_name
    field_descriptor.type = metadata.type

    if metadata.repeated:
        field_descriptor.label = FieldDescriptorProto.LABEL_REPEATED
        field_descriptor.options.packed = True
    else:
        field_descriptor.label = FieldDescriptorProto.LABEL_OPTIONAL

    if metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
        field_descriptor.type_name = metadata.message_type
    return field_descriptor


def _create_message_type(
    parameter_metadata: List[ParameterMetadata],
    message_name: str,
    file_descriptor: descriptor_pb2.FileDescriptorProto,
) -> None:
    """Creates a message type with fields intialized in 'file_descriptor'."""
    message_proto = file_descriptor.message_type.add()
    message_proto.name = message_name

    # Initialize the message with fields defined
    for i, metadata in enumerate(parameter_metadata):
        field_descriptor = _create_field(
            message_proto=message_proto, metadata=metadata, index=i + 1
        )
        if metadata.type == FieldDescriptorProto.TYPE_ENUM:
            _create_enum_type_class(
                file_descriptor=file_descriptor,
                parameter_metadata=metadata,
                field_descriptor=field_descriptor,
            )


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
    """
    try:
        pool.FindFileByName(service_name)
    except KeyError:
        file_descriptor = descriptor_pb2.FileDescriptorProto()
        file_descriptor.name = service_name
        file_descriptor.package = service_name
        _create_message_type(input_metadata, "Configurations", file_descriptor)
        _create_message_type(output_metadata, "Outputs", file_descriptor)
        pool.Add(file_descriptor)

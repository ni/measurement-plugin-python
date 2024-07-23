"""Serialization Descriptors."""

from enum import Enum
from json import loads
from typing import List

from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.descriptor_pb2 import DescriptorProto, FieldDescriptorProto

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter._get_type import (
    TYPE_FIELD_MAPPING,
)
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

    # True if enum is protobuf
    if not type(parameter_metadata.enum_type) is type(Enum):
        try:
            enum_type_name = parameter_metadata.enum_type.DESCRIPTOR.name
        except AttributeError:
            # Uses field name if DESCRIPTOR.name isn't defined
            name_sections = parameter_metadata.field_name.split("_")
            enum_type_name = "".join(section.capitalize() for section in name_sections)
    else:
        enum_type_name = parameter_metadata.enum_type.__name__

    if enum_type_name not in [file_enum.name for file_enum in file_descriptor.enum_type]:
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = enum_type_name
        for name, number in enum_dict.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = f"{enum_type_name}_{name}"
            enum_value_descriptor.number = number
    field_descriptor.type_name = enum_type_name


def _create_field(
    message_proto: DescriptorProto, metadata: ParameterMetadata, index: int
) -> FieldDescriptorProto:
    """Implement a field in 'message_proto'."""
    field_descriptor = message_proto.field.add()
    field_descriptor.number = index
    field_descriptor.name = metadata.field_name
    field_descriptor.type = TYPE_FIELD_MAPPING[metadata.type]

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
    """Creates two message types in one file descriptor proto."""
    try:
        pool.FindFileByName(service_name)
    except KeyError:
        file_descriptor = descriptor_pb2.FileDescriptorProto()
        file_descriptor.name = service_name
        file_descriptor.package = service_name
        _create_message_type(input_metadata, "Configurations", file_descriptor)
        _create_message_type(output_metadata, "Outputs", file_descriptor)
        pool.Add(file_descriptor)

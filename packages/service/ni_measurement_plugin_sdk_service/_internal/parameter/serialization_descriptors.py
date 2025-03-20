"""Serialization Descriptors."""

from __future__ import annotations

from enum import Enum, EnumMeta
from json import loads
from typing import TYPE_CHECKING, Union

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
)
from google.protobuf.descriptor_pool import DescriptorPool

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter._get_type import (
    TYPE_FIELD_MAPPING,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)

if TYPE_CHECKING:
    from google.protobuf.internal.enum_type_wrapper import _EnumTypeWrapper

    SupportedEnumType = Union[type[Enum], _EnumTypeWrapper]


def is_protobuf(enum_type: SupportedEnumType | None) -> bool:
    """Finds if 'enum_type' is a protobuf or a python enum."""
    return hasattr(enum_type, "ValueType")


def _get_enum_type_name(metadata: ParameterMetadata) -> str:
    """Get's enum type name from a 'parameter_metadata'."""
    enum_type = metadata.enum_type
    if enum_type is None:
        raise ValueError("Enum type cannot be None in ParameterMetadata.")

    if is_protobuf(enum_type) and not isinstance(enum_type, EnumMeta):
        return enum_type.DESCRIPTOR.name
    return enum_type.__name__


def _create_enum_type_class(
    file_descriptor: FileDescriptorProto,
    metadata: ParameterMetadata,
    field_descriptor: FieldDescriptorProto,
) -> None:
    """Implement a enum class in 'file_descriptor'."""
    enum_dict = loads(metadata.annotations[ENUM_VALUES_KEY])
    enum_type_name = _get_enum_type_name(metadata)

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
    parameter_metadata: list[ParameterMetadata],
    message_name: str,
    file_descriptor: FileDescriptorProto,
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
                metadata=metadata,
                field_descriptor=field_descriptor,
            )


def create_file_descriptor(
    service_name: str,
    output_metadata: list[ParameterMetadata],
    input_metadata: list[ParameterMetadata],
    pool: DescriptorPool,
) -> None:
    """Creates two message types in one file descriptor proto."""
    try:
        pool.FindFileByName(service_name)
    except KeyError:
        file_descriptor = FileDescriptorProto()
        file_descriptor.name = service_name
        file_descriptor.package = service_name
        _create_message_type(input_metadata, "Configurations", file_descriptor)
        _create_message_type(output_metadata, "Outputs", file_descriptor)
        pool.Add(file_descriptor)

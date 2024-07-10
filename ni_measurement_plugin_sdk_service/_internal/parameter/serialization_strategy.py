"""Serialization Strategy."""

import json
from enum import Enum
from typing import Any, Dict

from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._annotations import ENUM_VALUES_KEY
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from tests.utilities.stubs.loopback.types_pb2 import ProtobufColor


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
    enum_dict = json.loads(parameter_metadata.annotations[ENUM_VALUES_KEY])
    is_protobuf = _get_enum_type(parameter_metadata) is int

    if parameter_metadata.repeated:
        enum_type_name = parameter_metadata.default_value[0].__class__.__name__
    else:
        enum_type_name = parameter_metadata.default_value.__class__.__name__

    if (
        enum_type_name not in [enum_type.name for enum_type in file_descriptor.enum_type]
        and not is_protobuf
    ):
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = enum_type_name
        for name, number in enum_dict.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = name
            enum_value_descriptor.number = number

    if is_protobuf:
        field_descriptor.type_name = ProtobufColor.DESCRIPTOR.full_name
    else:
        field_descriptor.type_name = enum_type_name


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


def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        return type(parameter_metadata.default_value[0])
    else:
        return type(parameter_metadata.default_value)


def create_message_type(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    message_name: str,
    pool: descriptor_pool.DescriptorPool,
) -> Any:
    """Creates a message descriptor with the fields defined in a file descriptor proto.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

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
    for i in parameter_metadata_dict.keys():
        parameter_metadata = parameter_metadata_dict[i]
        field_descriptor = _create_field(
            message_proto=message_proto, metadata=parameter_metadata, index=i
        )
        if parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM:
            _create_enum_type(
                file_descriptor=file_descriptor,
                parameter_metadata=parameter_metadata,
                field_descriptor=field_descriptor,
            )
    pool.Add(file_descriptor)
    return pool.FindMessageTypeByName(f"{file_descriptor.package}.{message_proto.name}")


def get_enum_values(param: Any) -> Any:
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


def deserialize_enum_parameter(
    parameter_metadata: ParameterMetadata, message_instance: Any, field_name: str
) -> Any:
    """Convert all enums into the user defined enum type.

    Args:
        parameter_metadata (ParameterMetadata): Metadata of current enum value.

        message_instance (Any): Message class of all intialized fields.

        field_name (str): Name of current field.

    Returns:
        Any: Enum type or a list of enum types.
    """
    enum_dict = json.loads(parameter_metadata.annotations[ENUM_VALUES_KEY])
    field_value = getattr(message_instance, field_name)
    enum_type = _get_enum_type(parameter_metadata)
    if parameter_metadata.repeated:
        return [_get_enum_field(enum_dict, enum_type, value) for value in field_value]
    else:
        return _get_enum_field(enum_dict, enum_type, field_value)

# enums and default values
from enum import Enum
from typing import Any, Dict, Sequence
from uuid import uuid4

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from ni_measurement_plugin_sdk_service._internal.parameter.decoder_strategy import get_type_default
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from tests.utilities.stubs.loopback.types_pb2 import ProtobufColor


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_value (Sequence[Any]): Parameter values to serialize.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    pool = descriptor_pool.Default()
    file_descriptor_proto = descriptor_pb2.FileDescriptorProto()
    original_guid = str(uuid4())
    unique_descriptor_name = "msg" + "".join(filter(str.isalnum, original_guid))[:16]
    file_descriptor_proto.name = str(unique_descriptor_name)
    file_descriptor_proto.package = str(unique_descriptor_name)

    # Create a DescriptorProto for the message
    message_proto = file_descriptor_proto.message_type.add()
    message_proto.name = str(unique_descriptor_name)

    # Initialize the message with fields defined
    for i, parameter in enumerate(parameter_values, start=1):
        parameter_metadata = parameter_metadata_dict[i]
        is_python_enum = isinstance(parameter, Enum)
        # Define fields
        field_descriptor = _define_fields(
            message_proto=message_proto,
            metadata=parameter_metadata,
            index=i,
            param=parameter,
            is_python_enum=is_python_enum,
        )
        # define enums if it's a regular or a protobuf enum and there's a field
        if (
            parameter_metadata.type == FieldDescriptorProto.TYPE_ENUM
            and field_descriptor is not None
        ):
            _define_enums(
                file_descriptor=file_descriptor_proto,
                param=parameter,
                field_descriptor=field_descriptor,
            )

    # Get message and add fields to it
    pool.Add(file_descriptor_proto)
    message_descriptor = pool.FindMessageTypeByName(
        f"{unique_descriptor_name}.{unique_descriptor_name}"
    )
    message_instance = message_factory.GetMessageClass(message_descriptor)()

    # assign values to fields
    for i, parameter in enumerate(parameter_values, start=1):
        field_name = f"field_{i}"
        parameter_metadata = parameter_metadata_dict[i]
        parameter = _get_enum_values(param=parameter)
        try:
            if parameter_metadata.repeated:
                getattr(message_instance, field_name).extend(parameter)
            elif parameter_metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
                getattr(message_instance, field_name).CopyFrom(parameter)
            else:
                setattr(message_instance, field_name, parameter)
        except AttributeError:
            i += 1  # no field: parameter is None or equal to default value
    return message_instance.SerializeToString()


def serialize_default_values(parameter_metadata_dict: Dict[int, ParameterMetadata]) -> bytes:
    """Serialize the Default values in the Metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Configuration metadata.

    Returns:
        bytes: Serialized byte string containing default values.
    """
    default_value_parameter_array = [
        parameter.default_value for parameter in parameter_metadata_dict.values()
    ]
    return serialize_parameters(parameter_metadata_dict, default_value_parameter_array)


def _equal_to_default_value(metadata: ParameterMetadata, param: Any, is_python_enum: bool) -> bool:
    """Determine if 'param' is equal to it's default value.

    Args:
        metadata (ParameterMetadata): Metadata of 'param'.

        param (Any): A value/parameter of parameter_values.

        is_python_enum (boolean): True if 'param' is a enum from python's libraries.

    Returns:
        boolean: True if 'param' is equal it's default value or is None.
    """
    default_value = get_type_default(metadata.type, metadata.repeated)
    # gets value from a regular python enum
    if is_python_enum:
        if metadata.repeated:
            param = param[0].value
        else:
            param = param.value
    if param == default_value or param is None:
        return True
    return False


def _get_enum_values(param: Any) -> Any:
    """Get's value of an enum.

    Args:
        param (Any): A value/parameter of parameter_values.

    Returns:
        Any: An enum value or a list of enums or the 'param'.

    """
    if param == []:
        return param
    # if param is a list of enums, return values of them in a list
    # or param is an enum, returns the value of it
    # else it doesn nothing to param
    if isinstance(param, list) and isinstance(param[0], Enum):
        return [x.value for x in param]
    elif isinstance(param, Enum):
        return param.value
    return param


def _define_enums(
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
    # if param is a list, then it sets param to 1st element in list
    if isinstance(param, list):
        param = param[0]
    # if there are no enums/param is a different enum and is a python enum, defines a enum field
    if param.__class__.__name__ not in [
        enum.name for enum in file_descriptor.enum_type
    ] and isinstance(param, Enum):
        # Define a enum class
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = param.__class__.__name__

        # Add constants to enum class
        for name, number in param.__class__.__members__.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = name
            enum_value_descriptor.number = number.value
    # checks enum if it's protobuf or python
    try:
        field_descriptor.type_name = ProtobufColor.DESCRIPTOR.full_name
    except TypeError:
        field_descriptor.type_name = param.__class__.__name__


def _define_fields(
    message_proto: Any, metadata: ParameterMetadata, index: int, param: Any, is_python_enum: bool
) -> Any:
    """Implement a field in 'message_proto'.

    Args:
        message_proto (message_type): A message instance in 'file_descriptor_proto'.

        metadata (ParameterMetadata): Metadata of 'param'.

        index (int): 'param' index in parameter_values

        param (Any): A value/parameter of parameter_values.

        is_python_enum (boolean): True if 'param' is a enum from python's libraries.

    Returns:
        Any: field_descriptor of 'param' or None if 'param' is not equal_to_default_value.
    """
    # exits if param is None or eqaul to default value
    if not _equal_to_default_value(metadata=metadata, param=param, is_python_enum=is_python_enum):
        field_descriptor = message_proto.field.add()

        field_descriptor.number = index
        field_descriptor.name = f"field_{index}"
        field_descriptor.type = metadata.type
        # if a value is an array then it's labled as repeated and packed
        if metadata.repeated:
            field_descriptor.label = FieldDescriptorProto.LABEL_REPEATED
            field_descriptor.options.packed = True
        else:
            field_descriptor.label = FieldDescriptorProto.LABEL_OPTIONAL
        # if a value is a message then assign type name to it's full name
        if metadata.type == FieldDescriptorProto.TYPE_MESSAGE:
            field_descriptor.type_name = metadata.message_type
        return field_descriptor

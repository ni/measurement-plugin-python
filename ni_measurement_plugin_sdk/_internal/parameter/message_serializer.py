from typing import Any, Dict, Sequence
from uuid import uuid4
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

# metadata
from ni_measurement_plugin_sdk._internal.parameter.metadata import ParameterMetadata
from tests.unit.test_serializer import _get_test_parameter_by_id as currentParameter

# enums and default values
from enum import Enum, IntEnum
from ni_measurement_plugin_sdk._internal.parameter.serialization_strategy import get_type_default

def test() -> None:
    cur_values = [
                    2.0,
                    19.2,
                    3,
                    1,
                    2,
                    2,
                    True,
                    "TestString",
                    [5.5, 3.3, 1],
                    [5.5, 3.3, 1],
                    [1, 2, 3, 4],
                    [0, 1, 399],
                    [1, 2, 3, 4],
                    [0, 1, 399],
                    [True, False, True],
                    ["String1, String2"],
                    DifferentColor.ORANGE,
                    [DifferentColor.TEAL, DifferentColor.BROWN],
                    Countries.AUSTRALIA,
                    [Countries.AUSTRALIA, Countries.CANADA],
                ]
    
    # Serialize parameter_values using ParameterMetaData
    encoded_value_with_message = SerializeWithMessageInstance(
        parameter_metadata_dict=currentParameter(cur_values),
        parameter_values=cur_values)

    print()
    print(f"New Serialized value: {encoded_value_with_message}")


def SerializeWithMessageInstance(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any]
) -> bytes:

    # Creates a protobuf file to put descriptor stuff in
    pool = descriptor_pool.Default()
    file_descriptor_proto = descriptor_pb2.FileDescriptorProto()
    original_guid = uuid4()
    new_guid = 'msg' + ''.join(filter(str.isalnum, str(original_guid)))[:16]
    file_descriptor_proto.name = str(new_guid)
    file_descriptor_proto.package = str(new_guid)

    # Create a DescriptorProto for the message
    message_proto = file_descriptor_proto.message_type.add()
    message_proto.name = str(new_guid)

    # Define fields in message
    for i, parameter in enumerate(parameter_values, start=1):
        parameter_metadata = parameter_metadata_dict[i]
        is_enum = parameter_metadata.type == descriptor_pb2.FieldDescriptorProto.TYPE_ENUM

        # if value is an enum and a list, set parameter to the 1st element in value
        if is_enum and isinstance(parameter, list):
            parameter = parameter[0]
        # if value is not an enum and doesn't equal to it's default value, define fields
        if not is_enum or parameter.value != get_type_default(parameter_metadata.type, parameter_metadata.repeated):
            field_descriptor = message_proto.field.add()
            define_fields(
                field_descriptor=field_descriptor,
                metadata=parameter_metadata_dict,
                i=i
            )
            if is_enum:
                define_enums(
                    file_descriptor=file_descriptor_proto,
                    param=parameter,
                    field_descriptor=field_descriptor
                )
        
    # TODO: Learn how nested messages encode

    # Add fields to message and assign the message to a variable
    pool.Add(file_descriptor_proto)
    message_descriptor = pool.FindMessageTypeByName(str(new_guid) + '.' + str(new_guid))
    DynamicMessage = message_factory.GetMessageClass(message_descriptor)
    message_instance = DynamicMessage()

    #set fields to values and then serialize them
    for i, parameter in enumerate(parameter_values, start=1):
        try: 
            field_name = f"field_{i}"
            parameter = get_enum_values(param=parameter)
            if isinstance(parameter, list):
                repeated_field = getattr(message_instance, field_name)
                repeated_field.extend(parameter)
            else:
                setattr(message_instance, field_name, parameter)
        except:
            # goes here if enum is equal to it's default value
            i += 1

    serialized_value = message_instance.SerializeToString()
    return serialized_value

def get_enum_values(param):
    # if param is a list of enums, return values of them in a list 
    # or param is an enum, returns the value of it 
    # else it doesn nothing to param
    if isinstance(param, list) and isinstance(param[0], Enum):
        return [x.value for x in param]
    elif isinstance(param, Enum):
        return param.value
    return param

def define_enums(file_descriptor, param, field_descriptor):
    # if there are no enums or param is a different enum from ones defined before, creates a new enum
    if file_descriptor.enum_type == [] or param.__class__.__name__ not in [enum.name for enum in file_descriptor.enum_type]:
        # Define a enum class
        enum_descriptor = file_descriptor.enum_type.add()
        enum_descriptor.name = param.__class__.__name__
        field_descriptor.type_name = enum_descriptor.name

        # Add constants to enum class
        for name, number in param.__class__.__members__.items():
            enum_value_descriptor = enum_descriptor.value.add()
            enum_value_descriptor.name = name
            enum_value_descriptor.number = number.value
    else:
        field_descriptor.type_name = param.__class__.__name__ 

def define_fields(field_descriptor, metadata, i):
    parameter_metadata = metadata[i]

    field_descriptor.number = i
    field_descriptor.name = f"field_{i}"
    field_descriptor.type = parameter_metadata.type
    # if a value is an array then it's labled as repeated and packed
    if parameter_metadata.repeated:
        field_descriptor.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
        field_descriptor.options.packed = True 
    else:
        field_descriptor.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL



class DifferentColor(Enum):
    """Non-primary colors used for testing enum-typed config and output."""

    PURPLE = 0
    ORANGE = 1
    TEAL = 2
    BROWN = 3


class Countries(IntEnum):
    """Countries enum used for testing enum-typed config and output."""

    AMERICA = 0
    TAIWAN = 1
    AUSTRALIA = 2
    CANADA = 3

def main(**kwargs: Any) -> None:
    test()

if __name__ == "__main__":
    main()
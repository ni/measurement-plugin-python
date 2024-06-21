from typing import Any, Dict, Sequence
from uuid import uuid4
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FieldDescriptorProto as field

# metadata
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from tests.unit.test_serializer import _get_test_parameter_by_id as currentParameter

# enums and default values
from enum import Enum, IntEnum
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import xydata_pb2
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_strategy import get_type_default, _TYPE_DEFAULT_MAPPING

from tests.utilities.stubs.loopback.types_pb2 import ProtobufColor

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
                    double_xy_data,
                    double_xy_data_array
                ]
    
    # Serialize parameter_values using ParameterMetaData
    message_serializer = serialize_parameters(
        parameter_metadata_dict=currentParameter(cur_values),
        parameter_values=cur_values)

    print()
    print(f"Message Serialized value: {message_serializer}")


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
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

    # Initialize the message with fields defined
    for i, parameter in enumerate(parameter_values, start=1):
        parameter_metadata = parameter_metadata_dict[i]
        is_python_enum = isinstance(parameter, Enum)
        # Define fields
        field_descriptor = _define_fields(
            message_proto=message_proto,
            parameter_metadata=parameter_metadata,
            i=i,
            param=parameter,
            is_python_enum=is_python_enum)
        # define enums if it's a regular or a protobuf enum and there's a field
        if parameter_metadata.type == field.TYPE_ENUM and field_descriptor is not None:
            _define_enums(
                file_descriptor=file_descriptor_proto,
                param=parameter,
                field_descriptor=field_descriptor)

    # Get message and add fields to it
    pool.Add(file_descriptor_proto)
    message_descriptor = pool.FindMessageTypeByName(str(new_guid) + '.' + str(new_guid))
    message_instance = message_factory.GetMessageClass(message_descriptor)()

    #assign values to fields
    for i, parameter in enumerate(parameter_values, start=1):
        field_name = f"field_{i}"
        parameter_metadata = parameter_metadata_dict[i]
        parameter = _get_enum_values(param=parameter)
        try:
            if parameter_metadata.repeated:
                getattr(message_instance, field_name).extend(parameter)
            elif parameter_metadata.type == field.TYPE_MESSAGE:
                getattr(message_instance, field_name).CopyFrom(parameter)
            else:
                setattr(message_instance, field_name, parameter)
        except:
            i += 1 # no field: parameter is None or equal to default value
    return message_instance.SerializeToString()

def _equal_to_default_value(metadata, param, is_python_enum):
    default_value = get_type_default(
        metadata.type,
        metadata.repeated)
    # gets value from a regular python enum
    if is_python_enum:
        if metadata.repeated:
            param = param[0].value
        else:
            param = param.value
    # return true if param is None or eqaul to default value
    if param == default_value or param == None:
        return True
    return False

def _get_enum_values(param):
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

def _define_enums(file_descriptor, param, field_descriptor):
    # if param is a list, then it sets param to 1st element in list
    if isinstance(param, list):
        param = param[0]
    # if there are no enums/param is a different enum and is a python enum, defines a enum field
    if param.__class__.__name__ not in [enum.name for enum in file_descriptor.enum_type] and isinstance(param, Enum):
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
    except:
        field_descriptor.type_name = param.__class__.__name__ 

def _define_fields(message_proto, parameter_metadata, i, param, is_python_enum):
    # exits if param is None or eqaul to default value
    if not _equal_to_default_value(
        metadata=parameter_metadata,
        param=param,
        is_python_enum=is_python_enum):
        field_descriptor = message_proto.field.add()

        field_descriptor.number = i
        field_descriptor.name = f"field_{i}"
        field_descriptor.type = parameter_metadata.type
        # if a value is an array then it's labled as repeated and packed
        if parameter_metadata.repeated:
            field_descriptor.label = field.LABEL_REPEATED
            field_descriptor.options.packed = True 
        else:
            field_descriptor.label = field.LABEL_OPTIONAL
        # if a value is a message then assign type name to it's full name
        if parameter_metadata.type == field.TYPE_MESSAGE:
            field_descriptor.type_name = parameter_metadata.message_type
        return field_descriptor

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

double_xy_data = xydata_pb2.DoubleXYData()
double_xy_data.x_data.append(4)
double_xy_data.y_data.append(6)

double_xy_data2 = xydata_pb2.DoubleXYData()
double_xy_data2.x_data.append(8)
double_xy_data2.y_data.append(10)

double_xy_data_array = [double_xy_data, double_xy_data2]
# This should match the number of fields in bigmessage.proto.
BIG_MESSAGE_SIZE = 100

if __name__ == "__main__":
    test()
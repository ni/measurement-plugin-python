from typing import Any, Dict, Sequence
from uuid import uuid4
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

from ni_measurement_plugin_sdk._internal.parameter.metadata import ParameterMetadata
from tests.unit.test_serializer import _get_test_parameter_by_id as currentParameter

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
                ]
    
    # Serialize parameter_values using ParameterMetaData
    encoded_value_with_message = SerializeWithMessageInstance(
        parameter_metadata_dict=currentParameter(cur_values),
        parameter_values=cur_values)

    print()
    print(f"Serialized value: {encoded_value_with_message}")


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

    # Creates a new field for each parameter_value and defines it
    for i, value in enumerate(parameter_values, start=1):
        field_descriptor = message_proto.field.add()
        parameter_metadata = parameter_metadata_dict[i]

        field_descriptor.number = i
        field_descriptor.name = f"field_{i}"
        field_descriptor.type = parameter_metadata.type
        field_descriptor.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL

    # TODO: Learn how nested messages encode
    # TODO: Fix on encoding lists, uses varint and not length-delimited

    # Add fields to message and assign the message to a variable
    pool.Add(file_descriptor_proto)
    message_descriptor = pool.FindMessageTypeByName(str(new_guid) + '.' + str(new_guid))
    DynamicMessage = message_factory.GetMessageClass(message_descriptor)
    message_instance = DynamicMessage()

    #set fields to values and then serialize them
    for i, value in enumerate(parameter_values, start=1):
        field_name = f"field_{i}"
        setattr(message_instance, field_name, value)

    serialized_value = message_instance.SerializeToString()
    return serialized_value


def main(**kwargs: Any) -> None:
    test()

if __name__ == "__main__":
    main()
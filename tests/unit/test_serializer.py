"""Contains tests to validate serializer.py."""
import pytest
from google.protobuf import any_pb2
from google.protobuf import type_pb2

from ni_measurement_service._internal.parameter import serializer
from ni_measurement_service._internal.parameter.metadata import ParameterMetadata
from tests.assets import test_pb2


@pytest.mark.parametrize(
    "test_values",
    [
        [2.0, 19.2, 3, 1, 2, 2, True, "TestString", [5.5, 3.3, 1]],
        [-0.9999, -0.9999, -13, 1, 1000, 2, True, "////", [5.5, -13.3, 1, 0.0, -99.9999]],
    ],
)
def test___serializer___serialize_parameter___successful_serialization(test_values):
    """Validates if the custom serializer serializes data same as protobuf serialization.

    Args:
    ----
        test_values (List): List of values to be serialized.
        This should match the "MeasurementParameter" message defined in test.proto.

    """
    default_values = [2.0, 19.2, 3, 1, 2, 2, True, "TestString", [5.5, 3.3, 1]]
    parameter = _get_test_parameter_by_id(default_values)

    # Custom Serialization
    custom_serialized_bytes = serializer.serialize_parameters(parameter, test_values)

    _validate_serialized_bytes(custom_serialized_bytes, test_values)


@pytest.mark.parametrize(
    "default_values",
    [
        [2.0, 19.2, 3, 1, 2, 2, True, "TestString", [5.5, 3.3, 1]],
        [-0.9999, -0.9999, -13, 1, 1000, 2, True, "////", [5.5, -13.3, 1, 0.0, -99.9999]],
    ],
)
def test___serializer___serialize_default_parameter___successful_serialization(default_values):
    """Validates if the custom serializer serializes default values same as protobuf serialization.

    Args:
    ----
        default_values (List): Default values to be serialized.
        This should match the "MeasurementParameter" message defined in test.proto.

    """
    parameter = _get_test_parameter_by_id(default_values)

    # Custom Serialization
    custom_serialized_bytes = serializer.serialize_default_values(parameter)

    _validate_serialized_bytes(custom_serialized_bytes, default_values)


@pytest.mark.parametrize("values", [[2.0, 19.2, 3, 1, 2, 2, True, "TestString", [5.5, 3.3, 1.0]]])
def test___serializer___deserialize_parameter___successful_deserialization(values):
    """Validates if the custom deserializer deserializes data same as protobuf deserialization."""
    parameter = _get_test_parameter_by_id(values)
    grpc_serialized_data = _get_grpc_serialized_data(values)

    parameter_value_by_id = serializer.deserialize_parameters(parameter, grpc_serialized_data)

    assert list(parameter_value_by_id.values()) == values


def _validate_serialized_bytes(custom_serialized_bytes, values):
    # Serialization using gRPC Any
    grpc_serialized_data = _get_grpc_serialized_data(values)
    assert grpc_serialized_data == custom_serialized_bytes


def _get_grpc_serialized_data(values):
    grpc_parameter = _get_test_grpc_message(values)
    parameter_any = any_pb2.Any()
    parameter_any.Pack(grpc_parameter)
    grpc_serialized_data = parameter_any.value
    return grpc_serialized_data


def _get_test_parameter_by_id(default_values):
    parameter_by_id = {
        1: ParameterMetadata(
            display_name="float_data",
            type=type_pb2.Field.TYPE_FLOAT,
            repeated=False,
            default_value=default_values[0],
            annotations=None,
        ),
        2: ParameterMetadata(
            display_name="double_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=False,
            default_value=default_values[1],
            annotations=None,
        ),
        3: ParameterMetadata(
            display_name="int32_data",
            type=type_pb2.Field.TYPE_INT32,
            repeated=False,
            default_value=default_values[2],
            annotations=None,
        ),
        4: ParameterMetadata(
            display_name="uint32_data",
            type=type_pb2.Field.TYPE_INT64,
            repeated=False,
            default_value=default_values[3],
            annotations=None,
        ),
        5: ParameterMetadata(
            display_name="int64_data",
            type=type_pb2.Field.TYPE_UINT32,
            repeated=False,
            default_value=default_values[4],
            annotations=None,
        ),
        6: ParameterMetadata(
            display_name="uint64_data",
            type=type_pb2.Field.TYPE_UINT64,
            repeated=False,
            default_value=default_values[5],
            annotations=None,
        ),
        7: ParameterMetadata(
            display_name="bool_data",
            type=type_pb2.Field.TYPE_BOOL,
            repeated=False,
            default_value=default_values[6],
            annotations=None,
        ),
        8: ParameterMetadata(
            display_name="string_data",
            type=type_pb2.Field.TYPE_STRING,
            repeated=False,
            default_value=default_values[7],
            annotations=None,
        ),
        9: ParameterMetadata(
            display_name="double_array_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=True,
            default_value=default_values[8],
            annotations=None,
        ),
    }
    return parameter_by_id


def _get_test_grpc_message(test_values):
    parameter = test_pb2.MeasurementParameter()
    parameter.float_data = test_values[0]
    parameter.double_data = test_values[1]
    parameter.int32_data = test_values[2]
    parameter.uint32_data = test_values[3]
    parameter.int64_data = test_values[4]
    parameter.uint64_data = test_values[5]
    parameter.bool_data = test_values[6]
    parameter.string_data = test_values[7]
    parameter.double_array_data.extend(test_values[8])
    return parameter

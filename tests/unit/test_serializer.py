"""Contains tests to validate serializer.py."""
from enum import Enum

import pytest
from google.protobuf import any_pb2, type_pb2

from ni_measurementlink_service._internal.parameter import serializer
from ni_measurementlink_service._internal.parameter.metadata import (
    ParameterMetadata,
    TypeSpecialization,
)
from tests.assets import test_pb2


class DifferentColor(Enum):
    """Non-primary colors used for testing enum-typed config and output."""

    PURPLE = 0
    ORANGE = 1
    TEAL = 2
    BROWN = 3


@pytest.mark.parametrize(
    "test_values",
    [
        [
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
        ],
        [
            -0.9999,
            -0.9999,
            -13,
            1,
            1000,
            2,
            True,
            "////",
            [5.5, -13.3, 1, 0.0, -99.9999],
            [5.5, 3.3, 1],
            [1, 2, 3, 4],
            [0, 1, 399],
            [1, 2, 3, 4],
            [0, 1, 399],
            [True, False, True],
            ["String1, String2"],
            DifferentColor.ORANGE,
            [DifferentColor.TEAL, DifferentColor.BROWN],
        ],
    ],
)
def test___serializer___serialize_parameter___successful_serialization(test_values):
    default_values = test_values
    parameter = _get_test_parameter_by_id(default_values)

    # Custom Serialization
    custom_serialized_bytes = serializer.serialize_parameters(parameter, test_values)

    _validate_serialized_bytes(custom_serialized_bytes, test_values)


@pytest.mark.parametrize(
    "default_values",
    [
        [
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
        ],
        [
            -0.9999,
            -0.9999,
            -13,
            1,
            1000,
            2,
            True,
            "////",
            [5.5, -13.3, 1, 0.0, -99.9999],
            [5.5, 3.3, 1],
            [1, 2, 3, 4],
            [0, 1, 399],
            [1, 2, 3, 4],
            [0, 1, 399],
            [True, False, True],
            ["String1, String2"],
            DifferentColor.ORANGE,
            [DifferentColor.TEAL, DifferentColor.BROWN],
        ],
    ],
)
def test___serializer___serialize_default_parameter___successful_serialization(default_values):
    parameter = _get_test_parameter_by_id(default_values)

    # Custom Serialization
    custom_serialized_bytes = serializer.serialize_default_values(parameter)

    _validate_serialized_bytes(custom_serialized_bytes, default_values)


@pytest.mark.parametrize(
    "values",
    [
        [
            2.0,
            19.2,
            3,
            1,
            2,
            2,
            True,
            "TestString",
            [5.5, 3.3, 1.0],
            [5.5, 3, 1],
            [1, 2, 3, 4],
            [0, 1, 399],
            [1, 2, 3, 4],
            [0, 1, 399],
            [True, False, True],
            ["String1", "String2"],
            DifferentColor.ORANGE,
            [DifferentColor.TEAL, DifferentColor.BROWN],
        ]
    ],
)
def test___serializer___deserialize_parameter___successful_deserialization(values):
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
            annotations={},
        ),
        2: ParameterMetadata(
            display_name="double_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=False,
            default_value=default_values[1],
            annotations={},
        ),
        3: ParameterMetadata(
            display_name="int32_data",
            type=type_pb2.Field.TYPE_INT32,
            repeated=False,
            default_value=default_values[2],
            annotations={},
        ),
        4: ParameterMetadata(
            display_name="uint32_data",
            type=type_pb2.Field.TYPE_INT64,
            repeated=False,
            default_value=default_values[3],
            annotations={},
        ),
        5: ParameterMetadata(
            display_name="int64_data",
            type=type_pb2.Field.TYPE_UINT32,
            repeated=False,
            default_value=default_values[4],
            annotations={},
        ),
        6: ParameterMetadata(
            display_name="uint64_data",
            type=type_pb2.Field.TYPE_UINT64,
            repeated=False,
            default_value=default_values[5],
            annotations={},
        ),
        7: ParameterMetadata(
            display_name="bool_data",
            type=type_pb2.Field.TYPE_BOOL,
            repeated=False,
            default_value=default_values[6],
            annotations={},
        ),
        8: ParameterMetadata(
            display_name="string_data",
            type=type_pb2.Field.TYPE_STRING,
            repeated=False,
            default_value=default_values[7],
            annotations={},
        ),
        9: ParameterMetadata(
            display_name="double_array_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=True,
            default_value=default_values[8],
            annotations={},
        ),
        10: ParameterMetadata(
            display_name="float_array_data",
            type=type_pb2.Field.TYPE_FLOAT,
            repeated=True,
            default_value=default_values[9],
            annotations={},
        ),
        11: ParameterMetadata(
            display_name="int32_array_data",
            type=type_pb2.Field.TYPE_INT32,
            repeated=True,
            default_value=default_values[10],
            annotations={},
        ),
        12: ParameterMetadata(
            display_name="uint32_array_data",
            type=type_pb2.Field.TYPE_UINT32,
            repeated=True,
            default_value=default_values[11],
            annotations={},
        ),
        13: ParameterMetadata(
            display_name="int64_array_data",
            type=type_pb2.Field.TYPE_INT64,
            repeated=True,
            default_value=default_values[12],
            annotations={},
        ),
        14: ParameterMetadata(
            display_name="uint64_array_data",
            type=type_pb2.Field.TYPE_UINT64,
            repeated=True,
            default_value=default_values[13],
            annotations={},
        ),
        15: ParameterMetadata(
            display_name="bool_array_data",
            type=type_pb2.Field.TYPE_BOOL,
            repeated=True,
            default_value=default_values[14],
            annotations={},
        ),
        16: ParameterMetadata(
            display_name="string_array_data",
            type=type_pb2.Field.TYPE_STRING,
            repeated=True,
            default_value=default_values[15],
            annotations={},
        ),
        17: ParameterMetadata(
            display_name="enum_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=False,
            default_value=default_values[16],
            annotations={
                "ni/type_specialization": TypeSpecialization.Enum.value,
                "ni/enum.values": '{"PURPLE": 0, "ORANGE": 1, "TEAL": 2, "BROWN": 3}',
            },
        ),
        18: ParameterMetadata(
            display_name="enum_array_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=True,
            default_value=default_values[17],
            annotations={
                "ni/type_specialization": TypeSpecialization.Enum.value,
                "ni/enum.values": '{"PURPLE": 0, "ORANGE": 1, "TEAL": 2, "BROWN": 3}',
            },
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
    parameter.float_array_data.extend(test_values[9])
    parameter.int32_array_data.extend(test_values[10])
    parameter.uint32_array_data.extend(test_values[11])
    parameter.int64_array_data.extend(test_values[12])
    parameter.uint64_array_data.extend(test_values[13])
    parameter.bool_array_data.extend(test_values[14])
    parameter.string_array_data.extend(test_values[15])
    parameter.enum_data = test_values[16].value
    parameter.enum_array_data.extend(list(map(lambda x: x.value, test_values[17])))
    return parameter
"""Contains tests to validate serializer.py."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, IntEnum

import pytest
from google.protobuf import any_pb2, descriptor_pb2, descriptor_pool, type_pb2

from ni_measurement_plugin_sdk_service._annotations import (
    ENUM_VALUES_KEY,
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurement_plugin_sdk_service._internal.parameter import (
    decoder,
    serialization_descriptors,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
    TypeSpecialization,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    xydata_pb2,
)
from tests.utilities.stubs.serialization import test_pb2
from tests.utilities.stubs.serialization.bigmessage_pb2 import BigMessage


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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ]
    ],
)
def test___serializer___deserialize_parameter___successful_deserialization(values):
    parameter = _get_test_parameter_by_id(values)
    grpc_serialized_data = _get_grpc_serialized_data(values)
    service_name = _test_create_file_descriptor(list(parameter.values()), "deserialize_parameter")

    parameter_value_by_id = decoder.deserialize_parameters(
        parameter,
        grpc_serialized_data,
        service_name=service_name,
    )
    assert list(parameter_value_by_id.values()) == values


def test___empty_buffer___deserialize_parameters___returns_zero_or_empty():
    # Note that we set nonzero defaults to validate that we are getting zero-values
    # as opposed to simply getting the defaults.
    nonzero_defaults = [
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
        Countries.AUSTRALIA,
        [Countries.AUSTRALIA, Countries.CANADA],
        double_xy_data,
        double_xy_data_array,
    ]
    parameter = _get_test_parameter_by_id(nonzero_defaults)
    service_name = _test_create_file_descriptor(list(parameter.values()), "empty_buffer")
    parameter_value_by_id = decoder.deserialize_parameters(
        parameter, b"", service_name=service_name
    )

    for key, value in parameter_value_by_id.items():
        parameter_metadata = parameter[key]
        if parameter_metadata.repeated:
            assert value == list()
        elif parameter_metadata.type == type_pb2.Field.TYPE_ENUM:
            assert value.value == 0
        elif parameter_metadata.type == type_pb2.Field.TYPE_STRING:
            assert value == ""
        elif parameter_metadata.type == type_pb2.Field.TYPE_MESSAGE:
            assert value is None
        else:
            assert value == 0


def test___big_message___deserialize_parameters___returns_parameter_value_by_id() -> None:
    parameter_metadata_by_id = _get_big_message_metadata_by_id()
    values = [123.456 + i for i in range(BIG_MESSAGE_SIZE)]
    message = _get_big_message(values)
    serialized_data = message.SerializeToString()
    expected_parameter_value_by_id = {i + 1: value for (i, value) in enumerate(values)}
    service_name = _test_create_file_descriptor(
        list(parameter_metadata_by_id.values()), "big_message"
    )

    parameter_value_by_id = decoder.deserialize_parameters(
        parameter_metadata_by_id,
        serialized_data,
        service_name=service_name,
    )

    assert parameter_value_by_id == pytest.approx(expected_parameter_value_by_id)


def _get_grpc_serialized_data(values):
    grpc_parameter = _get_test_grpc_message(values)
    parameter_any = any_pb2.Any()
    parameter_any.Pack(grpc_parameter)
    grpc_serialized_data = parameter_any.value
    return grpc_serialized_data


def _get_test_parameter_by_id(default_values):
    parameter_by_id = {
        1: ParameterMetadata.initialize(
            display_name="float_data",
            type=type_pb2.Field.TYPE_FLOAT,
            repeated=False,
            default_value=default_values[0],
            annotations={},
        ),
        2: ParameterMetadata.initialize(
            display_name="double_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=False,
            default_value=default_values[1],
            annotations={},
        ),
        3: ParameterMetadata.initialize(
            display_name="int32_data",
            type=type_pb2.Field.TYPE_INT32,
            repeated=False,
            default_value=default_values[2],
            annotations={},
        ),
        4: ParameterMetadata.initialize(
            display_name="uint32_data",
            type=type_pb2.Field.TYPE_INT64,
            repeated=False,
            default_value=default_values[3],
            annotations={},
        ),
        5: ParameterMetadata.initialize(
            display_name="int64_data",
            type=type_pb2.Field.TYPE_UINT32,
            repeated=False,
            default_value=default_values[4],
            annotations={},
        ),
        6: ParameterMetadata.initialize(
            display_name="uint64_data",
            type=type_pb2.Field.TYPE_UINT64,
            repeated=False,
            default_value=default_values[5],
            annotations={},
        ),
        7: ParameterMetadata.initialize(
            display_name="bool_data",
            type=type_pb2.Field.TYPE_BOOL,
            repeated=False,
            default_value=default_values[6],
            annotations={},
        ),
        8: ParameterMetadata.initialize(
            display_name="string_data",
            type=type_pb2.Field.TYPE_STRING,
            repeated=False,
            default_value=default_values[7],
            annotations={},
        ),
        9: ParameterMetadata.initialize(
            display_name="double_array_data",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=True,
            default_value=default_values[8],
            annotations={},
        ),
        10: ParameterMetadata.initialize(
            display_name="float_array_data",
            type=type_pb2.Field.TYPE_FLOAT,
            repeated=True,
            default_value=default_values[9],
            annotations={},
        ),
        11: ParameterMetadata.initialize(
            display_name="int32_array_data",
            type=type_pb2.Field.TYPE_INT32,
            repeated=True,
            default_value=default_values[10],
            annotations={},
        ),
        12: ParameterMetadata.initialize(
            display_name="uint32_array_data",
            type=type_pb2.Field.TYPE_UINT32,
            repeated=True,
            default_value=default_values[11],
            annotations={},
        ),
        13: ParameterMetadata.initialize(
            display_name="int64_array_data",
            type=type_pb2.Field.TYPE_INT64,
            repeated=True,
            default_value=default_values[12],
            annotations={},
        ),
        14: ParameterMetadata.initialize(
            display_name="uint64_array_data",
            type=type_pb2.Field.TYPE_UINT64,
            repeated=True,
            default_value=default_values[13],
            annotations={},
        ),
        15: ParameterMetadata.initialize(
            display_name="bool_array_data",
            type=type_pb2.Field.TYPE_BOOL,
            repeated=True,
            default_value=default_values[14],
            annotations={},
        ),
        16: ParameterMetadata.initialize(
            display_name="string_array_data",
            type=type_pb2.Field.TYPE_STRING,
            repeated=True,
            default_value=default_values[15],
            annotations={},
        ),
        17: ParameterMetadata.initialize(
            display_name="enum_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=False,
            default_value=default_values[16],
            annotations={
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"PURPLE": 0, "ORANGE": 1, "TEAL": 2, "BROWN": 3}',
            },
            enum_type=DifferentColor,
        ),
        18: ParameterMetadata.initialize(
            display_name="enum_array_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=True,
            default_value=default_values[17],
            annotations={
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"PURPLE": 0, "ORANGE": 1, "TEAL": 2, "BROWN": 3}',
            },
            enum_type=DifferentColor,
        ),
        19: ParameterMetadata.initialize(
            display_name="int_enum_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=False,
            default_value=default_values[18],
            annotations={
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"AMERICA": 0, "TAIWAN": 1, "AUSTRALIA": 2, "CANADA": 3}',
            },
            enum_type=Countries,
        ),
        20: ParameterMetadata.initialize(
            display_name="int_enum_array_data",
            type=type_pb2.Field.TYPE_ENUM,
            repeated=True,
            default_value=default_values[19],
            annotations={
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"AMERICA": 0, "TAIWAN": 1, "AUSTRALIA": 2, "CANADA": 3}',
            },
            enum_type=Countries,
        ),
        21: ParameterMetadata.initialize(
            display_name="xy_data",
            type=type_pb2.Field.TYPE_MESSAGE,
            repeated=False,
            default_value=default_values[20],
            annotations={},
            message_type=xydata_pb2.DoubleXYData.DESCRIPTOR.full_name,
        ),
        22: ParameterMetadata.initialize(
            display_name="xy_data_array",
            type=type_pb2.Field.TYPE_MESSAGE,
            repeated=True,
            default_value=default_values[21],
            annotations={},
            message_type=xydata_pb2.DoubleXYData.DESCRIPTOR.full_name,
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
    parameter.int_enum_data = test_values[18].value
    parameter.int_enum_array_data.extend(list(map(lambda x: x.value, test_values[19])))
    parameter.xy_data.x_data.append(test_values[20].x_data[0])
    parameter.xy_data.y_data.append(test_values[20].y_data[0])
    parameter.xy_data_array.extend(test_values[21])
    return parameter


def _get_big_message_metadata_by_id() -> dict[int, ParameterMetadata]:
    return {
        i
        + 1: ParameterMetadata.initialize(
            display_name=f"field{i + 1}",
            type=type_pb2.Field.TYPE_DOUBLE,
            repeated=False,
            default_value=-1.0,
            annotations={},
        )
        for i in range(BIG_MESSAGE_SIZE)
    }


def _get_big_message(values: Sequence[float]) -> BigMessage:
    assert len(values) == BIG_MESSAGE_SIZE
    return BigMessage(**{f"field{i + 1}": value for (i, value) in enumerate(values)})


def _test_create_file_descriptor(metadata: list[ParameterMetadata], file_name: str) -> str:
    pool = descriptor_pool.Default()
    try:
        pool.FindMessageTypeByName(f"{file_name}.test")
    except KeyError:
        file_descriptor = descriptor_pb2.FileDescriptorProto()
        file_descriptor.name = file_name
        file_descriptor.package = file_name
        serialization_descriptors._create_message_type(metadata, "test", file_descriptor)
        pool.Add(file_descriptor)
    return file_name + ".test"

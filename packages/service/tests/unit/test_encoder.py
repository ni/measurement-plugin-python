"""Contains tests to validate serializer.py."""

from __future__ import annotations

from enum import Enum, IntEnum

import pytest
from google.protobuf import descriptor_pb2, descriptor_pool

from ni_measurement_plugin_sdk_service._internal.parameter import (
    encoder,
    metadata,
    serialization_descriptors,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    xydata_pb2,
)
from tests.unit.test_decoder import (
    _get_big_message,
    _get_big_message_metadata_by_id,
    _get_grpc_serialized_data,
    _get_test_parameter_by_id,
)
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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ],
        [
            -0.9999,
            -0.9999,
            -13,
            1,
            1000,
            2,
            True,
            "",
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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ],
    ],
)
def test___serializer___serialize_parameter___successful_serialization(test_values):
    default_values = test_values
    parameter = _get_test_parameter_by_id(default_values)
    service_name = _test_create_file_descriptor(list(parameter.values()), "serialize_parameter")

    # Custom Serialization
    custom_serialized_bytes = encoder.serialize_parameters(
        parameter,
        test_values,
        service_name=service_name,
    )

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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ],
        [
            -0.9999,
            -0.9999,
            -13,
            1,
            1000,
            2,
            False,
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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ],
    ],
)
def test___serializer___serialize_default_parameter___successful_serialization(default_values):
    parameter = _get_test_parameter_by_id(default_values)
    service_name = _test_create_file_descriptor(list(parameter.values()), "default_serialize")

    # Custom Serialization
    custom_serialized_bytes = encoder.serialize_default_values(parameter, service_name=service_name)

    _validate_serialized_bytes(custom_serialized_bytes, default_values)


def test___big_message___serialize_parameters___returns_serialized_data() -> None:
    parameter_metadata_by_id = _get_big_message_metadata_by_id()
    values = [123.456 + i for i in range(BIG_MESSAGE_SIZE)]
    expected_message = _get_big_message(values)
    service_name = _test_create_file_descriptor(
        list(parameter_metadata_by_id.values()), "big_message"
    )

    serialized_data = encoder.serialize_parameters(
        parameter_metadata_by_id,
        values,
        service_name=service_name,
    )

    message = BigMessage.FromString(serialized_data)
    assert message.ListFields() == pytest.approx(expected_message.ListFields())


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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ],
    ],
)
def test___serialize_parameter_multiple_times___returns_one_message_type(test_values):
    for i in range(100):
        test___serializer___serialize_parameter___successful_serialization(test_values)
    pool = descriptor_pool.Default()
    file_descriptor = pool.FindFileByName("serialize_parameter")
    message_dict = file_descriptor.message_types_by_name
    assert len(message_dict) == 1


def _validate_serialized_bytes(custom_serialized_bytes, values):
    # Serialization using gRPC Any
    grpc_serialized_data = _get_grpc_serialized_data(values)
    assert grpc_serialized_data == custom_serialized_bytes


def _test_create_file_descriptor(metadata: list[metadata.ParameterMetadata], file_name: str) -> str:
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

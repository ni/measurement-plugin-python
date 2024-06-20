import pytest

from ni_measurement_plugin_sdk._internal.parameter.message_serializer import SerializeWithMessageInstance as new_serializer
from tests.unit.test_serializer import _get_test_parameter_by_id as currentParameter
from ni_measurement_plugin_sdk._internal.parameter import serializer

from enum import Enum, IntEnum
from ni_measurement_plugin_sdk._internal.stubs.ni.protobuf.types import xydata_pb2

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
            double_xy_data_array
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
            Countries.AUSTRALIA,
            [Countries.AUSTRALIA, Countries.CANADA],
            double_xy_data,
            double_xy_data_array,
        ]
    ]
)

def test___serializer___serialize_parameter___successful_serialization(test_values):
    parameter = currentParameter(test_values)

    new_serialize = new_serializer(
        parameter_metadata_dict=parameter, 
        parameter_values=test_values,)
    current_serialize = serializer.serialize_parameters(
        parameter_metadata_dict=parameter, 
        parameter_values=test_values)

    print()
    print(f"Current Serializer: {current_serialize}")
    print()
    print(f"New Serializer: {new_serialize}")

    assert new_serialize == current_serialize

def main() -> None:
    test___serializer___serialize_parameter___successful_serialization(0)

if __name__ == "__main__":
    main()
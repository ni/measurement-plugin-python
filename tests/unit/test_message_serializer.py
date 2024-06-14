import pytest

from ni_measurement_plugin_sdk._internal.parameter.message_serializer import SerializeWithMessageInstance as new_serializer
from tests.unit.test_serializer import _get_test_parameter_by_id as currentParameter
from ni_measurement_plugin_sdk._internal.parameter import serializer

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
                    ],
                ]
)

def test___serializer___serialize_parameter___successful_serialization(test_values):
    default_values = test_values
    parameter = currentParameter(default_values)

    new_serialize = new_serializer(
        parameter_metadata_dict=parameter, 
        parameter_values=test_values)
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
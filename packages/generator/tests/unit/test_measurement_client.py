import pytest
from click import ClickException

from ni_measurement_plugin_sdk_generator.client._support import (
    _validate_and_transform_enum_annotations,
)


@pytest.mark.parametrize(
    "enum_annotations, expected_enum_annotations",
    [
        ('{"NONE": 0, "RED": 1, "GREEN": 2}', '{"NONE": 0, "RED": 1, "GREEN": 2}'),
        (
            '{"DC Volts": 0, "2-Wire Resistance": 1, "5 1/2": 2}',
            '{"DC_Volts": 0, "k_2_Wire_Resistance": 1, "k_5_1_2": 2}',
        ),
    ],
)
def test___enum_annotations___validate_and_transform_enum_annotations___returns_expected_enum_annotations(
    enum_annotations: str, expected_enum_annotations: str
) -> None:
    actual_enum_annotations = _validate_and_transform_enum_annotations(enum_annotations)

    assert actual_enum_annotations == expected_enum_annotations


def test___invalid_enum_annotations___validate_and_transform_enum_annotations___raises_invalid_enum_value_error() -> (
    None
):
    enum_annotations = '{"DC Volts": 0, "*": 1}'
    expected_error_message = "The enum value '*' is invalid."

    with pytest.raises(ClickException) as exc_info:
        _ = _validate_and_transform_enum_annotations(enum_annotations)

    assert exc_info.value.message == expected_error_message

"""Contains tests to validate metadata.py."""

from enum import Enum, IntEnum

import pytest

from ni_measurement_plugin_sdk_service import _datatypeinfo
from ni_measurement_plugin_sdk_service._annotations import (
    ENUM_VALUES_KEY,
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurement_plugin_sdk_service._internal.parameter import metadata
from ni_measurement_plugin_sdk_service.measurement.info import (
    DataType,
    TypeSpecialization,
)


class Color(Enum):
    """Primary colors used for testing enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class DifferentColor(Enum):
    """Non-primary colors used for testing enum-typed config and output."""

    NONE = 0
    ORANGE = 1
    TEAL = 2
    BROWN = 3


class Countries(IntEnum):
    """Countries enum used for testing IntEnum-typed config and output."""

    AMERICA = 0
    TAIWAN = 1
    AUSTRALIA = 2
    CANADA = 3


@pytest.mark.parametrize(
    "type,default_value,annotations",
    [
        (DataType.Int32, "string_default_value", {}),
        (DataType.Int32, 2.0, {}),
        (DataType.Boolean, 1, {}),
        (DataType.Boolean, 0, {}),
        (DataType.String, True, {}),
        (DataType.DoubleArray1D, 0.5, {}),
        (
            DataType.Enum,
            1.0,
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
        (
            DataType.Enum,
            DifferentColor.TEAL,
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
        (DataType.EnumArray1D, 1, {}),
        (
            DataType.EnumArray1D,
            [1.0, 2.0],
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
    ],
)
def test___default_value_different_from_type___validate___raises_type_exception(
    type, default_value, annotations
):
    data_type_info = _datatypeinfo.get_type_info(type)
    parameter_metadata = metadata.ParameterMetadata(
        "test_display_name",
        data_type_info.grpc_field_type,
        data_type_info.repeated,
        default_value,
        annotations,
    )

    with pytest.raises(TypeError):
        metadata._validate_default_value_type(parameter_metadata)


@pytest.mark.parametrize(
    "type,default_value,annotations",
    [
        (DataType.Int32, 1, {}),
        (DataType.Boolean, True, {}),
        (DataType.String, "string_default_value", {}),
        (DataType.DoubleArray1D, [0.5, 0.1], {}),
        (DataType.Double, 1.0, {}),
        (DataType.Double, 1, {}),
        (DataType.DoubleArray1D, [], {}),
        (
            DataType.Enum,
            Color.BLUE,
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
        (
            DataType.EnumArray1D,
            [Color.BLUE, Color.GREEN],
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
        (
            DataType.Enum,
            Countries.AUSTRALIA,
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"AMERICA":0, "TAIWAN": 1, "AUSTRALIA": 2, "CANADA": 3}',
            },
        ),
        (
            DataType.EnumArray1D,
            [Countries.AUSTRALIA, Countries.CANADA],
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"AMERICA":0, "TAIWAN": 1, "AUSTRALIA": 2, "CANADA": 3}',
            },
        ),
        (
            DataType.EnumArray1D,
            [],
            {
                TYPE_SPECIALIZATION_KEY: TypeSpecialization.Enum.value,
                ENUM_VALUES_KEY: '{"NONE":0, "RED": 1, "GREEN": 2, "BLUE": 3}',
            },
        ),
    ],
)
def test___default_value_same_as_type___validate___raises_no_exception(
    type, default_value, annotations
):
    data_type_info = _datatypeinfo.get_type_info(type)
    parameter_metadata = metadata.ParameterMetadata(
        "test_display_name",
        data_type_info.grpc_field_type,
        data_type_info.repeated,
        default_value,
        annotations,
    )

    metadata._validate_default_value_type(parameter_metadata)  # implicitly assert does not throw


@pytest.mark.parametrize(
    "display_name",
    [
        " test_string",
        "_____()!",
        "test@string",
        "",
    ],
)
def test___display_name_invalid_characters___validate___raises_value_exception(display_name):
    with pytest.raises(ValueError):
        metadata._validate_display_name(display_name)


@pytest.mark.parametrize(
    "display_name",
    [
        "teststring()",
        "tEsT StRIng?",
        "test_string!",
        "Test String: -10",
    ],
)
def test___display_name_valid_characters___validate___raises_no_exception(display_name):
    metadata._validate_display_name(display_name)

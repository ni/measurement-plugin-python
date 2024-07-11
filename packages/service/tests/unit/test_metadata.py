"""Contains tests to validate metadata.py."""

from enum import Enum, IntEnum

import pytest

from ni_measurement_plugin_sdk_service import _datatypeinfo
from ni_measurement_plugin_sdk_service._annotations import (
    ENUM_VALUES_KEY,
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurement_plugin_sdk_service._internal.parameter import metadata
from ni_measurement_plugin_sdk_service.measurement.info import DataType, TypeSpecialization


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
        (DataType.Double, 1, {}),
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
        metadata.validate_default_value_type(parameter_metadata)


@pytest.mark.parametrize(
    "type,default_value,annotations",
    [
        (DataType.Int32, 1, {}),
        (DataType.Boolean, True, {}),
        (DataType.String, "string_default_value", {}),
        (DataType.DoubleArray1D, [0.5, 0.1], {}),
        (DataType.Double, 1.0, {}),
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

    metadata.validate_default_value_type(parameter_metadata)  # implicitly assert does not throw

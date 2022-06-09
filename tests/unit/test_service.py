"""Tests to validated user facing decorators in service.py."""
import pytest

from ni_measurement_service.measurement.info import DataType
from ni_measurement_service.measurement.service import MeasurementService


def test___measurement_service___register_measurement_method___method_registered():
    """Test to validate register_measurement decorator."""
    measurement_service = MeasurementService(None, None)

    measurement_service.register_measurement(_fake_measurement_function)

    measurement_service.measure_function == _fake_measurement_function


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, True),
        ("StringConfiguration", DataType.String, "DefaultString"),
        ("DoubleConfiguration", DataType.Double, 0.899),
        ("Float", DataType.Float, 0.100),
        ("Double1DArray", DataType.DoubleArray1D, [1.009, -1.0009]),
        ("Int32", DataType.Int32, -8799),
        ("Int44", DataType.Int64, -999),
        ("UInt32", DataType.UInt32, 3994),
        ("UInt44", DataType.UInt64, 3456),
        ("UInt44", DataType.UInt64, False),
    ],
)
def test___measurement_service___add_configuration__configuration_added(
    display_name, type, default_value
):
    """Test to validate the configuration decorator."""
    measurement_service = MeasurementService(None, None)

    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        and param.default_value == default_value
        for param in measurement_service.configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, "MismatchDefaultValue"),
        ("StringConfiguration", DataType.String, True),
        ("DoubleConfiguration", DataType.Double, ""),
        ("Float", DataType.Float, 1),
        ("Double1DArray", DataType.DoubleArray1D, ""),
        ("Int32", DataType.Int32, 1.0),
        ("Int44", DataType.Int64, 1.0),
        ("UInt32", DataType.UInt32, [1.009, -1.0009]),
        ("UInt44", DataType.UInt64, ""),
    ],
)
def test___measurement_service___add_configuration_with_mismatch_default_value__raises_type_error(
    display_name, type, default_value
):
    """Test to validate the configuration decorator with default value mismatch."""
    measurement_service = MeasurementService(None, None)

    with pytest.raises(TypeError):
        measurement_service.configuration(display_name, type, default_value)(
            _fake_measurement_function
        )


@pytest.mark.parametrize(
    "display_name,type",
    [
        ("BoolConfiguration", DataType.Boolean),
        ("StringConfiguration", DataType.String),
        ("DoubleConfiguration", DataType.Double),
        ("Float", DataType.Float),
        ("Double1DArray", DataType.DoubleArray1D),
        ("Int32", DataType.Int32),
        ("Int44", DataType.Int64),
        ("UInt32", DataType.UInt32),
        ("UInt44", DataType.UInt64),
        ("UInt44", DataType.UInt64),
    ],
)
def test___measurement_service___add_output__output_added(display_name, type):
    """Test to validate the output decorator."""
    measurement_service = MeasurementService(None, None)

    measurement_service.output(display_name, type)(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        for param in measurement_service.output_parameter_list
    )


def _fake_measurement_function():
    pass

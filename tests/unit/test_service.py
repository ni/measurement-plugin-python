"""Tests to validated user facing decorators in service.py."""
import pathlib
from typing import List

import pytest

from ni_measurementlink_service.measurement.info import DataType, TypeSpecialization
from ni_measurementlink_service.measurement.service import MeasurementService


def test___measurement_service___register_measurement_method___method_registered(
    measurement_service: MeasurementService,
):
    """Test to validate register_measurement decorator."""
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
        ("Int64", DataType.Int64, -999),
        ("UInt32", DataType.UInt32, 3994),
        ("UInt64", DataType.UInt64, 3456),
        ("UInt64", DataType.UInt64, False),
    ],
)
def test___measurement_service___add_configuration__configuration_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        and param.default_value == default_value
        for param in measurement_service.configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value,instrument_type",
    [
        ("PinConfiguration", DataType.Pin, "Pin1", "test instrument"),
        ("PinArrayConfiguration", DataType.PinArray1D, ["Pin1", "Pin2"], "test instrument 2"),
    ],
)
def test___measurement_service___add_pin_configuration__pin_configuration_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
    instrument_type: str,
):
    measurement_service.configuration(
        display_name, type, default_value, instrument_type=instrument_type
    )(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        and param.default_value == default_value
        and param.annotations
        == {
            "ni/type_specialization": TypeSpecialization.Pin.value,
            "ni/pin.instrument_type": instrument_type,
        }
        for param in measurement_service.configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, True),
        ("StringConfiguration", DataType.String, "DefaultString"),
        ("DoubleConfiguration", DataType.Double, 0.899),
        ("Float", DataType.Float, 0.100),
        ("Double1DArray", DataType.DoubleArray1D, [1.009, -1.0009]),
        ("Int32", DataType.Int32, -8799),
        ("Int64", DataType.Int64, -999),
        ("UInt32", DataType.UInt32, 3994),
        ("UInt44", DataType.UInt64, 3456),
        ("UInt44", DataType.UInt64, False),
    ],
)
def test___measurement_service___add_non_pin_configuration__pin_type_annotations_not_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert not all(
        param.annotations.get("ni/type_specialization") == TypeSpecialization.Pin.value
        for param in measurement_service.configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("PathConfiguration", DataType.Path, "path1"),
        ("PathArrayConfiguration", DataType.PathArray1D, ["path1", "path2"]),
    ],
)
def test___measurement_service___add_path_configuration__path_configuration_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        and param.default_value == default_value
        and param.annotations
        == {
            "ni/type_specialization": TypeSpecialization.Path.value,
        }
        for param in measurement_service.configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, True),
        ("StringConfiguration", DataType.String, "DefaultString"),
        ("DoubleConfiguration", DataType.Double, 0.899),
        ("Float", DataType.Float, 0.100),
        ("Double1DArray", DataType.DoubleArray1D, [1.009, -1.0009]),
        ("Int32", DataType.Int32, -8799),
        ("Int64", DataType.Int64, -999),
        ("UInt32", DataType.UInt32, 3994),
        ("UInt64", DataType.UInt64, 3456),
    ],
)
def test___measurement_service___add_non_path_configuration__path_type_annotations_not_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
    """Test to validate the configuration decorator."""
    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert not all(
        param.annotations.get("ni/type_specialization") == TypeSpecialization.Path.value
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
        ("Int64", DataType.Int64, 1.0),
        ("UInt32", DataType.UInt32, [1.009, -1.0009]),
        ("UInt44", DataType.UInt64, ""),
        ("Pin", DataType.Pin, 1.0),
        ("Pin1DArray", DataType.PinArray1D, [1.009, -1.0009]),
        ("Path", DataType.Path, 1.0),
        ("Path1DArray", DataType.PathArray1D, [1.009, -1.0009]),
    ],
)
def test___measurement_service___add_configuration_with_mismatch_default_value__raises_type_error(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
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
        ("Int64", DataType.Int64),
        ("UInt32", DataType.UInt32),
        ("UInt44", DataType.UInt64),
        ("UInt44", DataType.UInt64),
    ],
)
def test___measurement_service___add_output__output_added(
    measurement_service: MeasurementService, display_name: str, type: DataType
):
    measurement_service.output(display_name, type)(_fake_measurement_function)

    assert any(
        param.display_name == display_name
        and param.type == type.value[0]
        and param.repeated == type.value[1]
        for param in measurement_service.output_parameter_list
    )


def _fake_measurement_function():
    pass


@pytest.mark.parametrize(
    "service_config,provided_interfaces",
    [
        (
            "example.serviceconfig",
            [
                "ni.measurementlink.measurement.v1.MeasurementService",
                "ni.measurementlink.measurement.v2.MeasurementService",
            ],
        ),
        ("example.v1.serviceconfig", ["ni.measurementlink.measurement.v1.MeasurementService"]),
        ("example.v2.serviceconfig", ["ni.measurementlink.measurement.v2.MeasurementService"]),
    ],
)
def test__measurement_service__create_measurement_service__service_info_populated_by_serviceconfig(
    test_assets_directory: str, service_config: str, provided_interfaces: List[str]
):
    measurement_service = MeasurementService(
        service_config_path=test_assets_directory / service_config,
        version="1.0.0.0",
        ui_file_paths=[],
    )

    assert measurement_service.service_info.service_class == "SampleMeasurement_Python"
    assert set(measurement_service.service_info.provided_interfaces) >= set(provided_interfaces)
    assert (
        measurement_service.service_info.description_url
        == "https://www.example.com/SampleMeasurement.html"
    )


@pytest.fixture
def measurement_service(test_assets_directory: str) -> MeasurementService:
    """Create a MeasurementService."""
    return MeasurementService(
        service_config_path=test_assets_directory / "example.serviceconfig",
        version="1.0.0.0",
        ui_file_paths=[],
    )

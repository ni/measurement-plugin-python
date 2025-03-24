"""Tests to validated user facing decorators in service.py."""

from __future__ import annotations

import pathlib
from enum import Enum

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service import _datatypeinfo
from ni_measurement_plugin_sdk_service._annotations import TYPE_SPECIALIZATION_KEY
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    xydata_pb2,
)
from ni_measurement_plugin_sdk_service.measurement.info import (
    DataType,
    TypeSpecialization,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService


class Color(Enum):
    """Primary colors used for testing enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class ColorWithoutZeroValue(Enum):
    """Enum with missing zero value used for testing enum-typed config and output."""

    RED = 1
    GREEN = 2
    BLUE = 3


double_xy_data = xydata_pb2.DoubleXYData()
double_xy_data.x_data.append(4)
double_xy_data.y_data.append(6)


def test___measurement_service___register_measurement_method___method_registered(
    measurement_service: MeasurementService,
):
    """Test to validate register_measurement decorator."""
    measurement_service.register_measurement(_fake_measurement_function)

    measurement_service._measure_function == _fake_measurement_function


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, True),
        ("StringConfiguration", DataType.String, "DefaultString"),
        ("DoubleConfiguration", DataType.Double, 0.899),
        ("Float", DataType.Float, 0.100),
        ("IntFloat", DataType.Float, 1),
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
    data_type_info = _datatypeinfo.get_type_info(type)

    assert any(
        param.display_name == display_name
        and param.type == data_type_info.grpc_field_type
        and param.repeated == data_type_info.repeated
        and param.default_value == default_value
        and param.message_type == data_type_info.message_type
        for param in measurement_service._configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value,instrument_type",
    [
        ("PinConfiguration", DataType.Pin, "Pin1", "test instrument"),
        ("PinArrayConfiguration", DataType.PinArray1D, ["Pin1", "Pin2"], "test instrument 2"),
    ],
)
def test___measurement_service___add_pin_configuration__pin_configuration_added_with_deprecation_warning(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
    instrument_type: str,
):
    with pytest.deprecated_call():
        measurement_service.configuration(
            display_name, type, default_value, instrument_type=instrument_type
        )(_fake_measurement_function)
    data_type_info = _datatypeinfo.get_type_info(type)

    assert any(
        param.display_name == display_name
        and param.type == data_type_info.grpc_field_type
        and param.repeated == data_type_info.repeated
        and param.default_value == default_value
        and param.annotations
        == {
            TYPE_SPECIALIZATION_KEY: TypeSpecialization.Pin.value,
            "ni/pin.instrument_type": instrument_type,
        }
        for param in measurement_service._configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value,instrument_type",
    [
        ("IOResourceConfiguration", DataType.IOResource, "Pin1", "test instrument"),
        (
            "IOResourceArrayConfiguration",
            DataType.IOResourceArray1D,
            ["Pin1", "Pin2"],
            "test instrument 2",
        ),
    ],
)
def test___measurement_service___add_ioresource_configuration__ioresource_configuration_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
    instrument_type: str,
):
    measurement_service.configuration(
        display_name, type, default_value, instrument_type=instrument_type
    )(_fake_measurement_function)
    data_type_info = _datatypeinfo.get_type_info(type)

    assert any(
        param.display_name == display_name
        and param.type == data_type_info.grpc_field_type
        and param.repeated == data_type_info.repeated
        and param.default_value == default_value
        and param.annotations
        == {
            TYPE_SPECIALIZATION_KEY: TypeSpecialization.IOResource.value,
            "ni/ioresource.instrument_type": instrument_type,
        }
        for param in measurement_service._configuration_parameter_list
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
        param.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.Pin.value
        for param in measurement_service._configuration_parameter_list
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
def test___measurement_service___add_non_ioresource_configuration__ioresource_type_annotations_not_added(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
):
    measurement_service.configuration(display_name, type, default_value)(_fake_measurement_function)

    assert not all(
        param.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.IOResource.value
        for param in measurement_service._configuration_parameter_list
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
    data_type_info = _datatypeinfo.get_type_info(type)

    assert any(
        param.display_name == display_name
        and param.type == data_type_info.grpc_field_type
        and param.repeated == data_type_info.repeated
        and param.default_value == default_value
        and param.annotations
        == {
            TYPE_SPECIALIZATION_KEY: TypeSpecialization.Path.value,
        }
        for param in measurement_service._configuration_parameter_list
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
        param.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.Path.value
        for param in measurement_service._configuration_parameter_list
    )


@pytest.mark.parametrize(
    "display_name,type,default_value",
    [
        ("BoolConfiguration", DataType.Boolean, "MismatchDefaultValue"),
        ("StringConfiguration", DataType.String, True),
        ("DoubleConfiguration", DataType.Double, ""),
        ("Double1DArray", DataType.DoubleArray1D, ""),
        ("Int32", DataType.Int32, 1.0),
        ("Int64", DataType.Int64, 1.0),
        ("UInt32", DataType.UInt32, [1.009, -1.0009]),
        ("UInt44", DataType.UInt64, ""),
        ("Pin", DataType.Pin, 1.0),
        ("Pin1DArray", DataType.PinArray1D, [1.009, -1.0009]),
        ("IOResource", DataType.IOResource, 1.0),
        ("IOResource1DArray", DataType.IOResourceArray1D, [1.009, -1.0009]),
        ("Path", DataType.Path, 1.0),
        ("Path1DArray", DataType.PathArray1D, [1.009, -1.0009]),
    ],
)
@pytest.mark.filterwarnings("ignore:.*Pin.*:DeprecationWarning")
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
        ("UInt64", DataType.UInt64),
        ("DoubleXYData", DataType.DoubleXYData),
        ("DoubleXYDataArray", DataType.DoubleXYDataArray1D),
        ("Double2DArray", DataType.Double2DArray),
        ("String2DArray", DataType.String2DArray),
    ],
)
def test___measurement_service___add_output__output_added(
    measurement_service: MeasurementService, display_name: str, type: DataType
):
    measurement_service.output(display_name, type)(_fake_measurement_function)
    data_type_info = _datatypeinfo.get_type_info(type)

    assert any(
        param.display_name == display_name
        and param.type == data_type_info.grpc_field_type
        and param.repeated == data_type_info.repeated
        and param.message_type == data_type_info.message_type
        for param in measurement_service._output_parameter_list
    )


def _fake_measurement_function():
    pass


no_annotations: dict[str, str] = {}


@pytest.mark.parametrize(
    "service_config,display_name,version,provided_interfaces,provided_annotations",
    [
        (
            "example.serviceconfig",
            "SampleMeasurement",
            "1.0.1",
            [
                "ni.measurementlink.measurement.v1.MeasurementService",
                "ni.measurementlink.measurement.v2.MeasurementService",
            ],
            {
                "ni/service.description": "Measure inrush current with a shorted load and validate results against configured limits.",
                "ni/service.collection": "CurrentTests.Inrush",
                "ni/service.tags": '["powerup","current"]',
            },
        ),
        (
            "example.v1.serviceconfig",
            "SampleMeasurement",
            "1.0.1",
            ["ni.measurementlink.measurement.v1.MeasurementService"],
            no_annotations,
        ),
        (
            "example.v2.serviceconfig",
            "SampleMeasurement",
            "1.0.3",
            ["ni.measurementlink.measurement.v2.MeasurementService"],
            no_annotations,
        ),
        (
            "example.OnlyCollection.serviceconfig",
            "SampleMeasurement",
            "1.0.4",
            ["ni.measurementlink.measurement.v2.MeasurementService"],
            {"ni/service.collection": "CurrentTests.Inrush"},
        ),
        (
            "example.OnlyTags.serviceconfig",
            "SampleMeasurement",
            "1.0.5",
            ["ni.measurementlink.measurement.v2.MeasurementService"],
            {"ni/service.tags": '["powerup","current","voltage"]'},
        ),
        (
            "example.AllAnnotations.serviceconfig",
            "SampleMeasurement",
            "1.0.6",
            ["ni.measurementlink.measurement.v2.MeasurementService"],
            {
                "ni/service.description": "Testing extra Client info",
                "client/extra.NumberID": "500",
                "client/extra.Parts": '["A25898","A25412"]',
                "client/extra.GroupName": '{"SpeakerType":"true","PhoneType":"false"}',
            },
        ),
        (
            "example.CustomAnnotations.serviceconfig",
            "SampleMeasurement",
            "1.0.7",
            ["ni.measurementlink.measurement.v1.MeasurementService"],
            {
                "description": "An annotated test measurement service.",
                "collection": "Tests.Measurements",
                "tags": '["test","measurement"]',
                "custom": '{"foo":"bar","baz":["qux","quux","quuux"],"snork":{"blarg":"flarp","oogle":'
                + '["foogle","boogle"],"ork":["zork","gork","bork"]}}',
            },
        ),
        (
            "example.localized.serviceconfig",
            "示例测量",
            "1.0.8",
            ["ni.measurementlink.measurement.v2.MeasurementService"],
            no_annotations,
        ),
    ],
)
def test___service_config___create_measurement_service___service_info_matches_service_config(
    test_assets_directory: pathlib.Path,
    service_config: str,
    display_name: str,
    version: str,
    provided_interfaces: list[str],
    provided_annotations: dict[str, str],
):
    measurement_service = MeasurementService(
        service_config_path=test_assets_directory / service_config,
        ui_file_paths=[],
    )

    assert measurement_service.service_info.display_name == display_name
    assert measurement_service.service_info.versions[0] == version
    assert measurement_service.service_info.service_class == "SampleMeasurement_Python"
    assert set(measurement_service.service_info.provided_interfaces) >= set(provided_interfaces)
    assert (
        measurement_service.service_info.description_url
        == "https://www.example.com/SampleMeasurement.html"
    )
    assert measurement_service.service_info.annotations == provided_annotations


def test___service_config___create_measurement_service_with_version___version_differs_from_service_config(
    test_assets_directory: pathlib.Path,
):
    with pytest.raises(RuntimeError) as version_error:
        with pytest.deprecated_call():
            MeasurementService(
                service_config_path=test_assets_directory / "example.serviceconfig",
                version="2.0.1",
            )

    assert "Version mismatch" in str(version_error.value)


def test___service_config___create_measurement_service_with_version___service_config_has_no_version(
    test_assets_directory: pathlib.Path,
):
    with pytest.deprecated_call():
        measurement_service = MeasurementService(
            service_config_path=test_assets_directory / "example.NoVersion.serviceconfig",
            version="2.0.1",
        )

    assert not measurement_service.service_info.versions[0]


@pytest.mark.parametrize(
    "service_config,version",
    [
        ("example.serviceconfig", "1.0.1"),
        ("example.v1.serviceconfig", "1.0.1"),
    ],
)
def test___service_config___create_measurement_service_with_version___version_is_used(
    test_assets_directory: pathlib.Path,
    service_config: str,
    version: str,
):
    with pytest.deprecated_call():
        service = MeasurementService(
            service_config_path=test_assets_directory / service_config,
            version=version,
        )

    assert service.service_info.versions[0] == version


@pytest.mark.parametrize(
    "display_name,type,default_value,enum_type",
    [
        ("EnumConfiguration", DataType.Enum, Color.GREEN, None),
        ("EnumConfiguration", DataType.Enum, ColorWithoutZeroValue.GREEN, ColorWithoutZeroValue),
    ],
)
def test___measurement_service___add_configuration_with_invalid_enum_type___raises_type_error(
    measurement_service: MeasurementService,
    display_name: str,
    type: DataType,
    default_value: object,
    enum_type: type[Enum],
):
    with pytest.raises(ValueError):
        measurement_service.configuration(display_name, type, default_value)(
            _fake_measurement_function
        )


def test___measurement_service___host_service_with_grpc_service_not_started___raises_error(
    measurement_service: MeasurementService,
    mocker: MockerFixture,
):
    measurement_service.register_measurement(_fake_measurement_function)
    mocker.patch(
        "ni_measurement_plugin_sdk_service._internal.service_manager.GrpcService.start",
        side_effect=Exception,
    )

    with pytest.raises(Exception):
        measurement_service.host_service()


@pytest.fixture
def measurement_service(test_assets_directory: pathlib.Path) -> MeasurementService:
    """Create a MeasurementService."""
    return MeasurementService(service_config_path=test_assets_directory / "example.serviceconfig")

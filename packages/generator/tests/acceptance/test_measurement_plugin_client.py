import importlib.util
import pathlib
from types import ModuleType
from typing import Generator, Union

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client

_TEST_MODULE_NAME = "test_measurement_client"


def test___measurement_plugin_client___measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    measurement_plugin_client_class = getattr(
        measurement_plugin_client_module, "MeasurementPlugInClient"
    )
    output = getattr(measurement_plugin_client_module, "Output")

    expected_measure_output = output(
        float_out=0.05999999865889549,
        double_array_out=[0.1, 0.2, 0.3],
        bool_out=False,
        string_out="sample string",
        string_array_out=["String1", "String2"],
        path_out="path/test",
        path_array_out=["path/test1", "path/ntest2"],
        io_out="resource",
        pin_array_out=["pin1", "pin2"],
        integer_out=10,
        xy_data_out=None,
    )

    measurement_plugin_client = measurement_plugin_client_class()
    measure_output = measurement_plugin_client.measure()

    assert measure_output == expected_measure_output


@pytest.fixture(scope="module")
def measurement_client_directory(
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: Generator[MeasurementService, None, None],
) -> pathlib.Path:
    """Test fixture that creates a measurement plugin-in client."""
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")

    with pytest.raises(SystemExit):
        create_client(
            [
                _TEST_MODULE_NAME,
                "--measurement-service-class",
                "ni.tests.TestMeasurement_Python",
                "--directory-out",
                temp_directory,
            ]
        )

    return temp_directory


@pytest.fixture(scope="module")
def measurement_plugin_client_module(
    measurement_client_directory: pathlib.Path,
) -> Union[ModuleType, None]:
    """Test fixture that imports the generated measurement plug-in client module."""
    module_path = measurement_client_directory / _TEST_MODULE_NAME / "measurement_plugin_client.py"
    spec = importlib.util.spec_from_file_location("measurement_plugin_client.py", module_path)
    if spec is not None:
        imported_module = importlib.util.module_from_spec(spec)
        if spec.loader is not None:
            spec.loader.exec_module(imported_module)
            return imported_module
        return None
    return None

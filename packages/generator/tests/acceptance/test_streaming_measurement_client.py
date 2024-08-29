import importlib.util
import pathlib
from types import ModuleType
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import streaming_data_measurement


def test___measurement_plugin_client___measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Output")
    expected_measure_output = output_type(
        name="<Name>",
        index=9,
        data=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    )
    measurement_plugin_client = test_measurement_client_type()

    measure_output = measurement_plugin_client.measure()

    assert measure_output == expected_measure_output


def test___measurement_plugin_client___stream_measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Output")
    measurement_plugin_client = test_measurement_client_type()

    measure_output = measurement_plugin_client.stream_measure()

    for count, output in enumerate(measure_output, start=0):
        expected_measure_output = output_type(
            name="<Name>",
            index=count,
            data=[i for i in range(count + 1)],
        )
        assert output == expected_measure_output


@pytest.fixture(scope="module")
def measurement_client_directory(
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> pathlib.Path:
    """Test fixture that creates a Measurement Plug-In Client."""
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"

    with pytest.raises(SystemExit):
        create_client(
            [
                "ni.tests.StreamingDataMeasurement_Python",
                "--module-name",
                module_name,
                "--class-name",
                "TestMeasurement",
                "--directory-out",
                temp_directory,
            ]
        )

    return temp_directory


@pytest.fixture(scope="module")
def measurement_plugin_client_module(
    measurement_client_directory: pathlib.Path,
) -> ModuleType:
    """Test fixture that imports the generated Measurement Plug-In Client module."""
    module_path = measurement_client_directory / "test_measurement_client.py"
    spec = importlib.util.spec_from_file_location("test_measurement_client.py", module_path)
    if spec is not None:
        imported_module = importlib.util.module_from_spec(spec)
        if spec.loader is not None:
            spec.loader.exec_module(imported_module)
            return imported_module
    pytest.fail("The module specification cannot be None.")


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with streaming_data_measurement.measurement_service.host_service() as service:
        yield service

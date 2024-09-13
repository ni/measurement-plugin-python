import importlib.util
import pathlib
from enum import Enum
from types import ModuleType
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import non_streaming_data_measurement


class EnumInEnum(Enum):
    """EnumInEnum used for enum-typed measurement configs and outputs."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


def test___measurement_plugin_client___measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        float_out=0.05999999865889549,
        double_array_out=[0.1, 0.2, 0.3],
        bool_out=False,
        string_out="sample string",
        string_array_out=["String1", "String2"],
        path_out="path/test",
        path_array_out=["path/test1", "path/ntest2"],
        io_out="resource",
        io_array_out=["resource1", "resource2"],
        integer_out=10,
        xy_data_out=None,
        enum_out=EnumInEnum.BLUE,
        enum_array_out=[EnumInEnum.RED, EnumInEnum.GREEN],
    )
    measurement_plugin_client = test_measurement_client_type()

    response = measurement_plugin_client.measure()

    # Enum values are not comparable due to differing imports.
    # So comparing values by converting them to string.
    assert str(response) == str(expected_output)


def test___measurement_plugin_client___stream_measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        float_out=0.05999999865889549,
        double_array_out=[0.1, 0.2, 0.3],
        bool_out=False,
        string_out="sample string",
        string_array_out=["String1", "String2"],
        path_out="path/test",
        path_array_out=["path/test1", "path/ntest2"],
        io_out="resource",
        io_array_out=["resource1", "resource2"],
        integer_out=10,
        xy_data_out=None,
        enum_out=EnumInEnum.BLUE,
        enum_array_out=[EnumInEnum.RED, EnumInEnum.GREEN],
    )
    measurement_plugin_client = test_measurement_client_type()

    response_iterator = measurement_plugin_client.stream_measure()

    responses = [response for response in response_iterator]
    assert len(responses) == 1
    # Enum values are not comparable due to differing imports.
    # So comparing values by converting them to string.
    assert str(responses[0]) == str(expected_output)


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
                "ni.tests.NonStreamingDataMeasurement_Python",
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
    with non_streaming_data_measurement.measurement_service.host_service() as service:
        yield service

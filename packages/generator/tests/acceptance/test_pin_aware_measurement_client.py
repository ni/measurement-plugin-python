import importlib.util
import pathlib
from types import ModuleType
from typing import Generator

import grpc
import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import pin_aware_measurement


def test___measurement_plugin_client___measure_with_pin_map_registration___returns_output(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = str(pin_map_directory / "1Smu1ChannelGroup1Pin1Site.pinmap")
    output_type = getattr(measurement_plugin_client_module, "Output")
    expected_output = output_type(
        pin_map_id=pin_map_path,
        sites=[0],
        session_names=["DCPower1/0"],
        resource_names=["DCPower1/0"],
        channel_lists=["DCPower1/0"],
    )
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    measurement_plugin_client.register_pin_map(pin_map_path)
    outputs = measurement_plugin_client.measure()

    assert outputs == expected_output


def test___measurement_plugin_client___measure_without_pin_map_registration___raises_no_sessions_error(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    with pytest.raises(grpc.RpcError) as exc_info:
        _ = measurement_plugin_client.measure()

    assert exc_info.value.code() == grpc.StatusCode.UNKNOWN
    assert "No sessions reserved." in (exc_info.value.details() or "")


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
                "ni.tests.PinAwareMeasurement_Python",
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
    with pin_aware_measurement.measurement_service.host_service() as service:
        yield service

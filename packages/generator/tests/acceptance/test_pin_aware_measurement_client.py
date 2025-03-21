import importlib.util
import pathlib
from collections.abc import Generator
from types import ModuleType

import grpc
import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from ni_measurement_plugin_sdk_service.session_management import PinMapContext

from tests.conftest import CliRunnerFunction
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import pin_aware_measurement


def test___measurement_plugin_client___measure_with_pin_map_registration___returns_output(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup1Pin1Site.pinmap"
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        pin_map_id=str(pin_map_path),
        sites=[0],
        session_names=["DCPower1/0"],
        resource_names=["DCPower1/0"],
        channel_lists=["DCPower1/0"],
    )
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    measurement_plugin_client.register_pin_map(pin_map_path)
    output = measurement_plugin_client.measure()

    assert output == expected_output


def test___measurement_plugin_client___measure_without_pin_map_registration___raises_no_sessions_error(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    with pytest.raises(grpc.RpcError) as exc_info:
        _ = measurement_plugin_client.measure()

    assert exc_info.value.code() == grpc.StatusCode.UNKNOWN
    assert "No sessions reserved." in (exc_info.value.details() or "")


def test___measurement_plugin_client___register_pin_map_without_pin_map_context___creates_pin_map_context_with_pin_map_id_and_sites(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    measurement_plugin_client.register_pin_map(pin_map_path)

    expected_pin_map_context = PinMapContext(pin_map_id=str(pin_map_path), sites=[0])
    assert measurement_plugin_client.pin_map_context == expected_pin_map_context


def test___measurement_plugin_client___register_pin_map_with_pin_map_context___updates_pin_map_context_with_pin_map_id(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measurement_plugin_client.pin_map_context = PinMapContext(pin_map_id="", sites=[0, 1])

    measurement_plugin_client.register_pin_map(pin_map_path)

    expected_pin_map_context = PinMapContext(pin_map_id=str(pin_map_path), sites=[0, 1])
    assert measurement_plugin_client.pin_map_context == expected_pin_map_context


def test___measurement_plugin_client___measure_with_default_site_selection___returns_selected_site(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup1Pin1Site.pinmap"
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measurement_plugin_client.register_pin_map(pin_map_path)

    output = measurement_plugin_client.measure()

    assert output.sites == [0]


def test___measurement_plugin_client___measure_with_multiple_sites_selection___returns_selected_sites(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measurement_plugin_client.register_pin_map(pin_map_path)

    measurement_plugin_client.sites = [0, 1]
    output = measurement_plugin_client.measure()

    assert output.sites == [0, 1]


def test___measurement_plugin_client___measure_with_invalid_sites_selection___raises_invalid_sites_error(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup1Pin1Site.pinmap"
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measurement_plugin_client.register_pin_map(pin_map_path)

    with pytest.raises(grpc.RpcError) as exc_info:
        measurement_plugin_client.sites = [0, 1]
        _ = measurement_plugin_client.measure()

    assert exc_info.value.code() == grpc.StatusCode.UNKNOWN
    assert 'Pin map does not contain site numbers: "1"' in (exc_info.value.details() or "")


def test___measurement_plugin_client___measure_with_pin_map_context___returns_output(
    measurement_plugin_client_module: ModuleType,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        pin_map_id=str(pin_map_path),
        sites=[0, 1],
        session_names=["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        resource_names=["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        channel_lists=["DCPower1/0, DCPower1/2"],
    )
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    measurement_plugin_client.pin_map_context = PinMapContext(
        pin_map_id=str(pin_map_path), sites=[0, 1]
    )
    output = measurement_plugin_client.measure()

    assert output == expected_output


@pytest.fixture(scope="module")
def measurement_client_directory(
    create_client: CliRunnerFunction,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> pathlib.Path:
    """Test fixture that creates a Measurement Plug-In Client."""
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"

    create_client(
        [
            "--measurement-service-class",
            "ni.tests.PinAwareMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "TestMeasurement",
            "--directory-out",
            str(temp_directory),
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

import importlib.util
import pathlib
import threading
import time
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
    expected_output = output_type(
        name="<Name>",
        index=9,
        data=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    )
    measurement_plugin_client = test_measurement_client_type()

    response = measurement_plugin_client.measure()

    assert response == expected_output


def test___measurement_plugin_client___stream_measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Output")
    measurement_plugin_client = test_measurement_client_type()

    response_iterator = measurement_plugin_client.stream_measure()

    responses = [response for response in response_iterator]
    expected_output = [
        output_type(
            name="<Name>",
            index=index,
            data=[data for data in range(index + 1)],
        )
        for index in range(10)
    ]
    assert responses == expected_output


def test___measurement_plugin_client___invoke_measure_from_two_threads___initiates_first_measure_and_rejects_second_measure(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    with pytest.raises(RuntimeError) as exc_info:
        measure_thread = threading.Thread(target=measurement_plugin_client.measure)
        measure_thread.start()
        measurement_plugin_client.measure()  # Calling Measure in main thread, to catch error in pytest.
        measure_thread.join()

    assert "A measure call is already in progress." in exc_info.value.args[0]


def test___non_streaming_measurement_execution___cancel___returns_true(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measure_thread = threading.Thread(target=measurement_plugin_client.measure)
    measure_thread.start()
    time.sleep(2)  # Wait for 2 seconds to call Cancel API.

    is_canceled = measurement_plugin_client.cancel()

    measure_thread.join()
    assert is_canceled


def test___streaming_measurement_execution___cancel___returns_true(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()
    measure_thread = threading.Thread(
        target=lambda: tuple(measurement_plugin_client.stream_measure())
    )
    measure_thread.start()
    time.sleep(2)  # Wait for 2 seconds to call Cancel API.

    is_canceled = measurement_plugin_client.cancel()

    measure_thread.join()
    assert is_canceled


def test___measurement_client___cancel_without__measure___returns_false(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    is_canceled = measurement_plugin_client.cancel()

    assert not is_canceled


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

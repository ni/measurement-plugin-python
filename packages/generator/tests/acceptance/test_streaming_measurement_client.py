import concurrent.futures
import importlib.util
import pathlib
from collections.abc import Generator
from types import ModuleType

import grpc
import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from tests.conftest import CliRunnerFunction
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import streaming_data_measurement


def test___measurement_plugin_client___measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Outputs")
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
    output_type = getattr(measurement_plugin_client_module, "Outputs")
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_measure_1 = executor.submit(measurement_plugin_client.measure)
            future_measure_2 = executor.submit(measurement_plugin_client.measure)
            future_measure_1.result()
            future_measure_2.result()

    expected_error_message = "A measurement is currently in progress. To make concurrent measurement requests, please create a new client instance."
    assert expected_error_message in exc_info.value.args[0]


def test___non_streaming_measurement_execution___cancel___cancels_measurement(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    with pytest.raises(grpc.RpcError) as exc_info:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            measure = executor.submit(measurement_plugin_client.measure)
            measurement_plugin_client.cancel()
            measure.result()

    assert exc_info.value.code() == grpc.StatusCode.CANCELLED


def test___streaming_measurement_execution___cancel___cancels_measurement(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    with pytest.raises(grpc.RpcError) as exc_info:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            measure = executor.submit(lambda: list(measurement_plugin_client.stream_measure()))
            measurement_plugin_client.cancel()
            measure.result()

    assert exc_info.value.code() == grpc.StatusCode.CANCELLED


def test___measurement_client___cancel_without_measure___returns_false(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    is_canceled = measurement_plugin_client.cancel()

    assert not is_canceled


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
            "ni.tests.StreamingDataMeasurement_Python",
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
    with streaming_data_measurement.measurement_service.host_service() as service:
        yield service

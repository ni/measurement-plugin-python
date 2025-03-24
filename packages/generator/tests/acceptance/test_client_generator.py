import os
import pathlib
import re
import sys
from collections.abc import Generator

import mypy.api
import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from tests.conftest import CliRunnerFunction
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import (
    non_streaming_data_measurement,
    streaming_data_measurement,
    void_measurement,
    localized_measurement,
)


def test___non_streaming_measurement___create_client___render_without_error(
    create_client: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    non_streaming_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.NonStreamingDataMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "NonStreamingDataMeasurementClient",
            "--directory-out",
            str(temp_directory),
        ]
    )

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___void_measurement___create_client___render_without_error(
    create_client: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    void_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "void_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.VoidMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "VoidMeasurementClient",
            "--directory-out",
            str(temp_directory),
        ]
    )

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___localized_measurement___create_client___render_without_error(
    create_client: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    localized_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "localized_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.LocalizedMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "LocalizedMeasurementClient",
            "--directory-out",
            str(temp_directory),
        ]
    )

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___all_registered_measurements___create_client___renders_without_error(
    create_client: CliRunnerFunction,
    tmp_path_factory: pytest.TempPathFactory,
    multiple_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")

    result = create_client(
        [
            "--all",
            "--directory-out",
            str(temp_directory),
        ]
    )

    expected_modules = [
        "non_streaming_data_measurement_client.py",
        "streaming_data_measurement_client.py",
    ]
    actual_modules = os.listdir(temp_directory)
    assert all(
        [
            result.exit_code == 0,
            len(actual_modules) == 2,
            expected_modules == actual_modules,
        ]
    )


def test___interactive_mode_with_registered_measurements___create_client___renders_without_error(
    create_client: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    non_streaming_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = "non_streaming_data_measurement_client.py"
    inputs = [
        "1",
        "non_streaming_data_measurement_client",
        "NonStreamingDataMeasurementClient",
        "x",
    ]
    os.chdir(temp_directory)

    result = create_client(["--interactive"], input="\n".join(inputs))

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___interactive_mode_without_registered_measurements___create_client___raises_exception(
    create_client: CliRunnerFunction,
) -> None:
    result = create_client(["--interactive"])
    assert result.exit_code == 1
    assert "No registered measurements." in str(result.exception)


def test___non_streaming_measurement___create_client___render_with_proper_line_ending(
    create_client: CliRunnerFunction,
    tmp_path_factory: pytest.TempPathFactory,
    non_streaming_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    filename = f"{module_name}.py"

    result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.NonStreamingDataMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "NonStreamingDataMeasurementClient",
            "--directory-out",
            str(temp_directory),
        ]
    )

    assert result.exit_code == 0
    _assert_line_ending(temp_directory / filename)


def test___non_streaming_measurement___create_client___render_without_mypy_error(
    create_client: CliRunnerFunction,
    tmp_path_factory: pytest.TempPathFactory,
    non_streaming_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    filename = f"{module_name}.py"

    result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.NonStreamingDataMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "NonStreamingDataMeasurementClient",
            "--directory-out",
            str(temp_directory),
        ]
    )

    mypy_result = mypy.api.run([str(temp_directory / filename)])
    mypy_exit_status = mypy_result[2]
    assert result.exit_code == 0
    assert mypy_exit_status == 0


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path) -> None:
    expected = expected_path.read_text(encoding="utf-8")
    result = result_path.read_text(encoding="utf-8")

    assert expected == result


def _assert_line_ending(file_path: pathlib.Path) -> None:
    content = file_path.read_bytes()
    if sys.platform == "win32":
        pattern = re.compile(rb"(\r?\n)+")
        matches = pattern.findall(content)
        for match in matches:
            assert match == b"\r\n"
    else:
        pattern = re.compile(rb"\r?\n")
        matches = pattern.findall(content)
        for match in matches:
            assert match == b"\n"


@pytest.fixture
def non_streaming_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a non streaming Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def void_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a void Measurement Plug-In Service."""
    with void_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def localized_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a localized Measurement Plug-In Service."""
    with localized_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def multiple_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service(), streaming_data_measurement.measurement_service.host_service() as services:
        yield services

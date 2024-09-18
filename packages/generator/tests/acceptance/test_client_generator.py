from functools import partial
import os
import pathlib
import re
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from click.testing import Result
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import non_streaming_data_measurement, streaming_data_measurement


def test___command_line_args___create_client___render_without_error(
    create_client: partial[Result],
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    result: Result = create_client(
        [
            "--measurement-service-class",
            "ni.tests.NonStreamingDataMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "NonStreamingDataMeasurementClient",
            "--directory-out",
            temp_directory,
        ]
    )

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___command_line_args___create_client_for_all_registered_measurements___renders_without_error(
    create_client: partial[Result],
    tmp_path_factory: pytest.TempPathFactory,
    multiple_measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")

    result: Result = create_client(
        [
            "--all",
            "--directory-out",
            temp_directory,
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


def test___command_line_args_with_registered_measurements___create_client_using_interactive_mode___renders_without_error(
    create_client: partial[Result],
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = "non_streaming_data_measurement_client.py"
    os.chdir(temp_directory)

    with patch(
        "click.prompt",
        side_effect=[
            "1",
            "non_streaming_data_measurement_client",
            "NonStreamingDataMeasurementClient",
            "x",
        ],
    ):
        result: Result = create_client(["--interactive"])

    assert result.exit_code == 0
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___command_line_args_without_registering_any_measurement___create_client_using_interactive_mode___raises_exception(
    create_client: partial[Result],
) -> None:
    result: Result = create_client(["--interactive"])
    assert result.exit_code == 1
    assert "No registered measurements." in str(result.exception)


def test___command_line_args___create_client___render_with_proper_line_ending(
    create_client: partial[Result],
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    filename = f"{module_name}.py"

    result: Result = create_client(
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


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path) -> None:
    expected = expected_path.read_text()
    result = result_path.read_text()

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
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def multiple_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service(), streaming_data_measurement.measurement_service.host_service() as services:
        yield services

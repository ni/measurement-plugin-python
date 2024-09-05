import pathlib
import re
import sys
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import non_streaming_data_measurement


def test___command_line_args___create_client___render_without_error(
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                "ni.tests.NonStreamingDataMeasurement_Python",
                "--module-name",
                module_name,
                "--class-name",
                "NonStreamingDataMeasurementClient",
                "--directory-out",
                temp_directory,
            ]
        )

    assert not exc_info.value.code
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___command_line_args___create_client_for_all_active_measurement___render_without_error(
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = "non_streaming_data_measurement_client.py"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                "--all",
                "--directory-out",
                temp_directory,
            ]
        )

    assert not exc_info.value.code
    _assert_equal(
        golden_path / filename,
        temp_directory / filename,
    )


def test___command_line_args___create_client___render_with_proper_line_ending(
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "non_streaming_data_measurement_client"
    filename = f"{module_name}.py"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                "ni.tests.NonStreamingDataMeasurement_Python",
                "--module-name",
                module_name,
                "--class-name",
                "NonStreamingDataMeasurementClient",
                "--directory-out",
                temp_directory,
            ]
        )

    assert not exc_info.value.code
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


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service() as service:
        yield service

import pathlib
import re
import sys

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client


def test___command_line_args___create_client___render_without_error(
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"
    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = f"{module_name}.py"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                "--module-name",
                module_name,
                "--class-name",
                "TestMeasurement",
                "--measurement-service-class",
                "ni.tests.TestMeasurement_Pytho",
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
    module_name = "test_measurement_client"
    filename = f"{module_name}.py"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                "--module-name",
                module_name,
                "--class-name",
                "TestMeasurement",
                "--measurement-service-class",
                "ni.tests.TestMeasurement_Python",
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
        pattern = re.compile(r"\r?\n")
        matches = pattern.findall(content)
        for match in matches:
            assert match == b"\n"

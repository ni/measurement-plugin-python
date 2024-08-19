import pathlib
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.client import create_client


def test___command_line_args___create_client___render_without_error(
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: Generator[MeasurementService, None, None],
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"

    with pytest.raises(SystemExit) as exc_info:
        create_client(
            [
                module_name,
                "--measurement-service-class",
                "ni.tests.TestMeasurement_Python",
                "--directory-out",
                temp_directory,
            ]
        )

    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"
    filename = "measurement_plugin_client.py"

    assert not exc_info.value.code
    _assert_equal(
        golden_path / filename,
        temp_directory / module_name / filename,
    )


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path) -> None:
    expected = expected_path.read_text()
    result = result_path.read_text()

    assert expected == result

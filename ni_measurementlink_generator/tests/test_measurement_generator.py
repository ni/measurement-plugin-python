"""Tests to validate the python measurement generator."""
import pathlib

import pytest

from ni_measurementlink_generator import template

test_assets_path = pathlib.Path(__file__).parent / "test_assets"


def test___command_line_args___create_measurement___render_without_exception(tmpdir):
    """Given example command line args when create_measurement assert renders without exceptions."""
    temp_directory = pathlib.Path(tmpdir.mkdir("measurement_files"))

    with pytest.raises(SystemExit):
        template.create_measurement(
            [
                "SampleMeasurement",
                "--measurement-version",
                "1.0.0.0",
                "--ui-file",
                "MeasurementUI.measui",
                "--service-class",
                "SampleMeasurement_Python",
                "--description-url",
                "https://www.example.com/SampleMeasurement.html",
                "--directory-out",
                temp_directory,
            ]
        )

    golden_path = test_assets_path / "example_renders"

    filenames = ["measurement.py", "SampleMeasurement.serviceconfig", "start.bat"]
    for filename in filenames:
        _assert_equal(
            golden_path / filename,
            temp_directory / filename,
        )


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path):
    expected = expected_path.read_text()
    result = result_path.read_text()

    assert expected == result

import pathlib

import pytest

from ni_measurementlink_generator import template


def test___command_line_args___create_measurement___render_without_exception(
    test_assets_directory: pathlib.Path, tmp_path_factory: pytest.TempPathFactory
):
    temp_directory = tmp_path_factory.mktemp("measurement_files")

    with pytest.raises(SystemExit):
        template.create_measurement(
            [
                "Sample Measurement",
                "--measurement-version",
                "1.2.3.4",
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

    golden_path = test_assets_directory / "example_renders"

    filenames = ["measurementWithAnnotations.py", "SampleMeasurement.serviceconfig", "start.bat"]
    for filename in filenames:
        _assert_equal(
            golden_path / filename,
            temp_directory / filename,
        )


def test___command_line_args___create_measurement_with_annotations___render_without_exception(
    test_assets_directory: pathlib.Path, tmp_path_factory: pytest.TempPathFactory
):
    temp_directory = tmp_path_factory.mktemp("measurement_files")

    with pytest.raises(SystemExit):
        template.create_measurement(
            [
                "Sample Measurement With Annotations",
                "--measurement-version",
                "1.2.3.4",
                "--ui-file",
                "MeasurementUI.measui",
                "--service-class",
                "SampleMeasurement_Python",
                "--description-url",
                "https://www.example.com/SampleMeasurement.html",
                "--directory-out",
                temp_directory,
                "--annotations-description",
                "Measurement description",
                "--collection",
                "Measurement collection",
                "--tags",
                "M1",
                "--tags",
                "M2",
                "--tags",
                "M3",
            ]
        )

    golden_path = test_assets_directory / "example_renders"

    filenames = [
        "measurementWithAnnotations.py",
        "SampleMeasurementWithAnnotations.serviceconfig",
        "start.bat",
    ]
    for filename in filenames:
        golden_file = golden_path / filename
        # We always generate only measurement.py
        if filename == "measurementWithAnnotations.py":
            filename = "measurement.py"

        _assert_equal(golden_file, temp_directory / filename)


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path):
    expected = expected_path.read_text()
    result = result_path.read_text()

    assert expected == result

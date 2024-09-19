import pathlib

import pytest

from tests.conftest import CliRunnerFunction


def test___command_line_args___create_measurement___render_without_error(
    create_measurement: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_files")
    golden_path = test_assets_directory / "example_renders" / "measurement"
    filenames = ["measurement.py", "SampleMeasurement.serviceconfig", "start.bat", "_helpers.py"]

    result = create_measurement(
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
            str(temp_directory),
        ]
    )

    assert result.exit_code == 0
    for filename in filenames:
        _assert_equal(
            golden_path / filename,
            temp_directory / filename,
        )


def test___command_line_args___create_measurement_with_annotations___render_without_error(
    create_measurement: CliRunnerFunction,
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_files")

    result = create_measurement(
        [
            "Sample Measurement",
            "--measurement-version",
            "1.2.3.4",
            "--ui-file",
            "MeasurementUI.measui",
            "--service-class",
            "SampleMeasurement_Python",
            "-D",
            "Measurement description",
            "--description-url",
            "https://www.example.com/SampleMeasurement.html",
            "--directory-out",
            str(temp_directory),
            "--collection",
            "Measurement.Collection",
            "--tags",
            "M1",
            "--tags",
            "M2",
            "--tags",
            "M3",
        ]
    )

    golden_path = test_assets_directory / "example_renders" / "measurement_with_annotations"

    filenames = ["measurement.py", "SampleMeasurement.serviceconfig", "start.bat", "_helpers.py"]
    assert result.exit_code == 0
    for filename in filenames:
        _assert_equal(
            golden_path / filename,
            temp_directory / filename,
        )


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path) -> None:
    expected = expected_path.read_text()
    result = result_path.read_text()

    assert expected == result

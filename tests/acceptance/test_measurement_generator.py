"""Tests to validate the python measurement generator."""
import pathlib
import sys

generator_path = pathlib.Path(
    pathlib.Path(__file__).resolve().parent.parent.parent / "measurement_generator"
)
sys.path.append(str(generator_path))

from template import _create_measurement


def test___command_line_args___create_measurement___render_without_exception(tmpdir):
    """Tests to validate command line args and render calls using a sample measurement."""

    temp_directory = tmpdir.mkdir("measurement_files")
    _create_measurement.callback(
        "SampleMeasurement",
        "1.0.0.0",
        "Sample",
        "Sample",
        "measurementUI.measui",
        "SampleMeasurement_Python",
        "{E0095551-CB4B-4352-B65B-4280973694B2}",
        "description",
        temp_directory,
    )

    golden_path = generator_path / "example_renders"

    _assert_equal(
        golden_path / "example_py.json",
        temp_directory / "SampleMeasurement.py",
    )
    _assert_equal(
        golden_path / "example_serviceconfig.json",
        temp_directory / "SampleMeasurement.serviceConfig",
    )


def _read_file(file_path):
    with file_path.open("r") as fout:
        return fout.read()


def _assert_equal(expected_path, result_path):
    expected = _read_file(expected_path)
    
    result = _read_file(result_path)

    assert expected == result

"""Tests to validate the python measurement generator."""
import pathlib
import sys

generator_path = pathlib.Path(
    pathlib.Path(__file__).resolve().parent.parent.parent / "measurement_generator"
)
sys.path.append(str(generator_path))

from template import _create_measurement


def test___command_line_args___create_measurement___render_without_exception(tmpdir):
    """Given example command line args when create_measurement assert renders without excpetions."""

    temp_directory = pathlib.Path(tmpdir.mkdir("measurement_files"))
    _create_measurement.callback(
        "SampleMeasurement", # display name
        "1.0.0.0", # version
        "Measurement", # measurement type
        "Product", # product type 
        "measurementUI.measui", # UI file
        "SampleMeasurement_Python", # service class
        "{E0095551-CB4B-4352-B65B-4280973694B2}", # GUID
        "description", # description
        temp_directory, # output directory
    )

    golden_path = generator_path / "example_renders"

    _assert_equal(
        golden_path / "example_py.py",
        temp_directory / "measurement.py",
    )
    _assert_equal(
        golden_path / "example_serviceconfig.serviceConfig",
        temp_directory / "SampleMeasurement.serviceConfig",
    )


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path):
    expected = expected_path.read_text()
    result = result_path.read_text()
    
    assert expected == result
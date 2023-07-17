"""Contains Test Doubles related to Measurement service. """
import pathlib
from enum import Enum

import ni_measurementlink_service as nims


class Color(Enum):
    """Primary colors used for example enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


fake_service_directory = pathlib.Path(__file__).resolve().parent.parent.parent
fake_measurement_service = nims.MeasurementService(
    service_config_path=fake_service_directory
    / "examples/sample_measurement/SampleMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        fake_service_directory / "examples/sample_measurement/SampleMeasurement.measui",
        fake_service_directory / "examples/sample_measurement/SampleAllParameters.measui",
        fake_service_directory / "examples/sample_measurement/SampleMeasurement.vi",
    ],
)


@fake_measurement_service.register_measurement
@fake_measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@fake_measurement_service.configuration(
    "Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3]
)
@fake_measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@fake_measurement_service.configuration("String In", nims.DataType.String, "sample string")
@fake_measurement_service.configuration("Enum In", nims.DataType.Enum, Color.BLUE, enum_type=Color)
@fake_measurement_service.configuration(
    "String Array In", nims.DataType.StringArray1D, ["String1", "String2"]
)
@fake_measurement_service.output("Float out", nims.DataType.Float)
@fake_measurement_service.output("Double Array out", nims.DataType.DoubleArray1D)
@fake_measurement_service.output("Bool out", nims.DataType.Boolean)
@fake_measurement_service.output("String out", nims.DataType.String)
@fake_measurement_service.output("Enum out", nims.DataType.Enum, enum_type=Color)
@fake_measurement_service.output("String Array out", nims.DataType.StringArray1D)
def measure(
    self, float_input, double_array_input, bool_input, string_input, enum_input, string_array_in
):
    """Perform a loopback measurement with various data types."""
    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input
    enum_output = enum_input
    string_array_out = string_array_in

    return (
        float_output,
        float_array_output,
        bool_output,
        string_output,
        enum_output,
        string_array_out,
    )

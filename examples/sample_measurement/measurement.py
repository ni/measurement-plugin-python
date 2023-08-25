"""Perform a loopback measurement with various data types."""
import logging
import pathlib
import sys
from enum import Enum

import click
from _helpers import configure_logging, verbosity_option

try:
    from _stubs import color_pb2
except ImportError:
    from examples.sample_measurement._stubs import color_pb2  # type: ignore

import ni_measurementlink_service as nims

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
sample_measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "SampleMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory / "SampleMeasurement.measui",
        service_directory / "SampleAllParameters.measui",
        service_directory / "SampleMeasurement.vi",
    ],
)


class Color(Enum):
    """Primary colors used for example enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


@sample_measurement_service.register_measurement
@sample_measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@sample_measurement_service.configuration(
    "Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3]
)
@sample_measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@sample_measurement_service.configuration("String In", nims.DataType.String, "sample string")
@sample_measurement_service.configuration(
    "Enum In", nims.DataType.Enum, Color.BLUE, enum_type=Color
)
@sample_measurement_service.configuration(
    "Protobuf Enum In",
    nims.DataType.Enum,
    color_pb2.ProtobufColor.BLACK,
    enum_type=color_pb2.ProtobufColor,
)
@sample_measurement_service.configuration(
    "String Array In", nims.DataType.StringArray1D, ["String1", "String2"]
)
@sample_measurement_service.output("Float out", nims.DataType.Float)
@sample_measurement_service.output("Double Array out", nims.DataType.DoubleArray1D)
@sample_measurement_service.output("Bool out", nims.DataType.Boolean)
@sample_measurement_service.output("String out", nims.DataType.String)
@sample_measurement_service.output("Enum out", nims.DataType.Enum, enum_type=Color)
@sample_measurement_service.output(
    "Protobuf Enum out", nims.DataType.Enum, enum_type=color_pb2.ProtobufColor
)
@sample_measurement_service.output("String Array out", nims.DataType.StringArray1D)
def measure(
    float_input,
    double_array_input,
    bool_input,
    string_input,
    enum_input,
    protobuf_enum_input,
    string_array_in,
):
    """Perform a loopback measurement with various data types."""
    logging.info("Executing measurement")

    def cancel_callback():
        logging.info("Canceling measurement")

    sample_measurement_service.context.add_cancel_callback(cancel_callback)

    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input
    enum_output = enum_input
    protobuf_enum_output = protobuf_enum_input
    string_array_out = string_array_in
    logging.info("Completed measurement")

    return (
        float_output,
        float_array_output,
        bool_output,
        string_output,
        enum_output,
        protobuf_enum_output,
        string_array_out,
    )


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a loopback measurement with various data types."""
    configure_logging(verbosity)

    with sample_measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

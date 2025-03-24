"""Perform a loopback measurement with various data types."""

import logging
import pathlib
import sys
from collections.abc import Iterable
from enum import Enum

import _array_utils
import click
import ni_measurement_plugin_sdk_service as nims
from _helpers import configure_logging, verbosity_option
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)

try:
    from _stubs import color_pb2
except ImportError:
    from examples.sample_measurement._stubs import color_pb2  # type: ignore

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "SampleMeasurement.serviceconfig",
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


# Define a list of lists of floats
_list_of_lists_of_floats = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]

# Convert the list of lists to a Double2DArray
_converted_double_2d_array = _array_utils.list_to_double2darray(_list_of_lists_of_floats)

# Define a list of lists of strings
_list_of_lists_of_string = [["String1", "String2", "String3"], ["String4", "String5", "String6"]]

# Convert the list of lists to a String2DArray
_converted_string_2d_array = _array_utils.list_to_string2darray(_list_of_lists_of_string)


@measurement_service.register_measurement
@measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@measurement_service.configuration("Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3])
@measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@measurement_service.configuration("String In", nims.DataType.String, "sample string")
@measurement_service.configuration("Enum In", nims.DataType.Enum, Color.BLUE, enum_type=Color)
@measurement_service.configuration(
    "Protobuf Enum In",
    nims.DataType.Enum,
    color_pb2.ProtobufColor.BLACK,
    enum_type=color_pb2.ProtobufColor,
)
@measurement_service.configuration(
    "String Array In", nims.DataType.StringArray1D, ["String1", "String2"]
)
@measurement_service.output("Float out", nims.DataType.Float)
@measurement_service.output("Double Array out", nims.DataType.DoubleArray1D)
@measurement_service.output("Bool out", nims.DataType.Boolean)
@measurement_service.output("String out", nims.DataType.String)
@measurement_service.output("Enum out", nims.DataType.Enum, enum_type=Color)
@measurement_service.output(
    "Protobuf Enum out", nims.DataType.Enum, enum_type=color_pb2.ProtobufColor
)
@measurement_service.output("String Array out", nims.DataType.StringArray1D)
@measurement_service.output("Double 2D Array Out", nims.DataType.Double2DArray)
@measurement_service.output("Converted Double 2D Array", nims.DataType.Double2DArray)
@measurement_service.output("String 2D Array Out", nims.DataType.String2DArray)
@measurement_service.output("Converted String 2D Array", nims.DataType.String2DArray)
def measure(
    float_input: float,
    double_array_input: Iterable[float],
    bool_input: bool,
    string_input: str,
    enum_input: Color,
    protobuf_enum_input: color_pb2.ProtobufColor.ValueType,
    string_array_in: Iterable[str],
) -> tuple[
    float,
    Iterable[float],
    bool,
    str,
    Color,
    color_pb2.ProtobufColor.ValueType,
    Iterable[str],
    array_pb2.Double2DArray,
    array_pb2.Double2DArray,
    array_pb2.String2DArray,
    array_pb2.String2DArray,
]:
    """Perform a loopback measurement with various data types."""
    logging.info("Executing measurement")

    def cancel_callback() -> None:
        logging.info("Canceling measurement")

    measurement_service.context.add_cancel_callback(cancel_callback)

    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input
    enum_output = enum_input
    protobuf_enum_output = protobuf_enum_input
    string_array_output = string_array_in
    double_2d_array_output = array_pb2.Double2DArray(
        rows=2, columns=3, data=[1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    )
    converted_double_2d_array_output = _converted_double_2d_array
    string_2d_array_output = array_pb2.String2DArray(
        rows=2, columns=3, data=["ABC", "DEF", "GHI", "JKL", "MNO", "PQR"]
    )
    converted_string_2d_array_output = _converted_string_2d_array
    logging.info("Completed measurement")

    return (
        float_output,
        float_array_output,
        bool_output,
        string_output,
        enum_output,
        protobuf_enum_output,
        string_array_output,
        double_2d_array_output,
        converted_double_2d_array_output,
        string_2d_array_output,
        converted_string_2d_array_output,
    )


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a loopback measurement with various data types."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

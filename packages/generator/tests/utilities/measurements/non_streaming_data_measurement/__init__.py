"""Contains utility functions to test loopback measurement service. """

from pathlib import Path
from typing import Iterable, Tuple

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import xydata_pb2


service_directory = Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NonStreamingDataMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@measurement_service.configuration("Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3])
@measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@measurement_service.configuration("String In", nims.DataType.String, "sample string")
@measurement_service.configuration(
    "String Array In", nims.DataType.StringArray1D, [
        "string with /forwardslash", 
        "string with \\backslash", 
        "string with 'single quotes'", 
        'string with "double quotes"', 
        "string with \ttabspace",
        "string with \nnewline",
    ]
)
@measurement_service.configuration("Path In", nims.DataType.Path, "sample\\path\\for\\test")
@measurement_service.configuration(
    "Path Array In", nims.DataType.PathArray1D, [
        "path/with/forward/slash", 
        "path\\with\\backslash", 
        "path with 'single quotes'", 
        'path with "double quotes"', 
        "path\twith\ttabs",
        "path\nwith\nnewlines",
    ]
)
@measurement_service.configuration("IO In", nims.DataType.IOResource, "resource")
@measurement_service.configuration(
    "IO Array In", nims.DataType.IOResourceArray1D, ["resource1", "resource2"]
)
@measurement_service.configuration("Integer In", nims.DataType.Int32, 10)
@measurement_service.output("Float out", nims.DataType.Float)
@measurement_service.output("Double Array out", nims.DataType.DoubleArray1D)
@measurement_service.output("Bool out", nims.DataType.Boolean)
@measurement_service.output("String out", nims.DataType.String)
@measurement_service.output("String Array out", nims.DataType.StringArray1D)
@measurement_service.output("Path Out", nims.DataType.Path)
@measurement_service.output("Path Array Out", nims.DataType.PathArray1D)
@measurement_service.output("IO Out", nims.DataType.IOResource)
@measurement_service.output("IO Array Out", nims.DataType.IOResourceArray1D)
@measurement_service.output("Integer Out", nims.DataType.Int32)
@measurement_service.output("XY Data Out", nims.DataType.DoubleXYData)
def measure(
    float_input: float,
    double_array_input: Iterable[float],
    bool_input: bool,
    string_input: str,
    string_array_input: Iterable[str],
    path_input: Path,
    path_array_input: Iterable[Path],
    io_input: str,
    io_array_input: Iterable[str],
    integer_input: int,
) -> Tuple[
    float,
    Iterable[float],
    bool,
    str,
    Iterable[str],
    Path,
    Iterable[Path],
    str,
    Iterable[str],
    int,
    xydata_pb2.DoubleXYData,
]:
    """Perform a loopback measurement with various data types."""
    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input
    string_array_output = string_array_input
    path_output = path_input
    path_array_output = path_array_input
    io_output = io_input
    io_array_output = io_array_input
    integer_output = integer_input
    xy_data_output = xydata_pb2.DoubleXYData()

    return (
        float_output,
        float_array_output,
        bool_output,
        string_output,
        string_array_output,
        path_output,
        path_array_output,
        io_output,
        io_array_output,
        integer_output,
        xy_data_output,
    )

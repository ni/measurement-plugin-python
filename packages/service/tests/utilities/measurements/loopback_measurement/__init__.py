"""Contains utility functions to test loopback measurement service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable
from enum import Enum
from typing import Tuple

import ni_measurement_plugin_sdk_service as nims
from tests.utilities.measurements.sample_measurement._stubs import color_pb2


class Color(Enum):
    """Primary colors used for example enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "LoopbackMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


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
def measure(
    float_input: float,
    double_array_input: Iterable[float],
    bool_input: bool,
    string_input: str,
    enum_input: Color,
    protobuf_enum_input: color_pb2.ProtobufColor.ValueType,
    string_array_in: Iterable[str],
) -> tuple[
    float, Iterable[float], bool, str, Color, color_pb2.ProtobufColor.ValueType, Iterable[str]
]:
    """Perform a loopback measurement with various data types."""
    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input
    enum_output = enum_input
    protobuf_enum_output = protobuf_enum_input
    string_array_out = string_array_in

    return (
        float_output,
        float_array_output,
        bool_output,
        string_output,
        enum_output,
        protobuf_enum_output,
        string_array_out,
    )

"""Contains utility functions to test loopback measurement service with non-ASCII characters."""

from collections.abc import Iterable
from enum import Enum
from pathlib import Path

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
    xydata_pb2,
)

from tests.utilities.measurements.non_streaming_data_measurement._stubs import color_pb2

service_directory = Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "LocalizedMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


class Color(Enum):
    """用于示例枚举类型配置和输出的主要颜色."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


@measurement_service.register_measurement
@measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@measurement_service.configuration("Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3])
@measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@measurement_service.configuration("String In", nims.DataType.String, "示例字符串")
@measurement_service.configuration(
    "String Array In",
    nims.DataType.StringArray1D,
    [
        "带有/正斜杠的字符串",
        "带有\\反斜杠的字符串",
        "带有'单引号'的字符串",
        '带有"双引号"的字符串',
        "带有\t制表符的字符串",
        "带有\n换行符的字符串",
    ],
)
@measurement_service.configuration("Path In", nims.DataType.Path, "示例\\路径\\用于\\测试")
@measurement_service.configuration(
    "Path Array In",
    nims.DataType.PathArray1D,
    [
        "路径/带有/正斜杠",
        "路径\\带有\\反斜杠",
        "路径 带有 '单引号'",
        '路径 带有 "双引号"',
        "路径\t带有\t制表符",
        "路径\n带有\n换行符",
    ],
)
@measurement_service.configuration("IO In", nims.DataType.IOResource, "资源")
@measurement_service.configuration(
    "IO Array In", nims.DataType.IOResourceArray1D, ["资源1", "资源2"]
)
@measurement_service.configuration("Integer In", nims.DataType.Int32, 10)
@measurement_service.configuration("Enum In", nims.DataType.Enum, Color.BLUE, enum_type=Color)
@measurement_service.configuration(
    "Enum Array In", nims.DataType.EnumArray1D, [1, 2], enum_type=Color
)
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
@measurement_service.output("Enum Out", nims.DataType.Enum, enum_type=Color)
@measurement_service.output("Enum Array Out", nims.DataType.EnumArray1D, enum_type=Color)
@measurement_service.output("Double 2D Array out", nims.DataType.Double2DArray)
@measurement_service.output("String 2D Array out", nims.DataType.String2DArray)
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
    enum_input: Color,
    enum_array_input: Iterable[Color],
) -> tuple[
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
    Color,
    Iterable[Color],
    array_pb2.Double2DArray,
    array_pb2.String2DArray,
]:
    """使用各种数据类型执行环回测量."""
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
    enum_output = enum_input
    enum_array_output = enum_array_input
    double_2d_array_output = array_pb2.Double2DArray(
        rows=2, columns=3, data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    )
    string_2d_array_output = array_pb2.String2DArray(
        rows=2, columns=3, data=["你好", "世界", "测试", "中文", "本地化", "字符串"]
    )

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
        enum_output,
        enum_array_output,
        double_2d_array_output,
        string_2d_array_output,
    )

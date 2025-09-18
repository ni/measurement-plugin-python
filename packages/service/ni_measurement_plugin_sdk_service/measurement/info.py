"""Measurement service metadata classes and enums."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import NamedTuple

from ni.measurementlink.discovery.v1.client import ServiceInfo

__all__ = ["ServiceInfo", "MeasurementInfo", "TypeSpecialization", "DataType"]


class MeasurementInfo(NamedTuple):
    """A named tuple providing information about a measurement."""

    display_name: str
    """The user visible name of the measurement."""

    version: str
    """The current version of the measurement."""

    ui_file_paths: list[Path]
    """Absolute paths to user interface files for the measurement (e.g. ``.measui`` or ``.vi``
    files)."""


class TypeSpecialization(enum.Enum):
    """Enum that represents the type specializations for measurement parameters."""

    NoType = ""
    Pin = "pin"
    Path = "path"
    Enum = "enum"
    IOResource = "ioresource"


class DataType(enum.Enum):
    """Enum that represents the supported data types."""

    Int32 = 0
    Int64 = 1
    UInt32 = 2
    UInt64 = 3
    Float = 4
    Double = 5
    Boolean = 6
    String = 7
    Pin = 8
    Path = 9
    Enum = 10
    DoubleXYData = 11
    IOResource = 12
    Double2DArray = 13
    String2DArray = 14

    Int32Array1D = 100
    Int64Array1D = 101
    UInt32Array1D = 102
    UInt64Array1D = 103
    FloatArray1D = 104
    DoubleArray1D = 105
    BooleanArray1D = 106
    StringArray1D = 107
    PinArray1D = 108
    PathArray1D = 109
    EnumArray1D = 110
    DoubleXYDataArray1D = 111
    IOResourceArray1D = 112

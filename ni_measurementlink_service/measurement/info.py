"""Contains classes and enums to represent measurement metadata."""
from __future__ import annotations

import enum
from pathlib import Path
from typing import Dict, List, NamedTuple


class MeasurementInfo(NamedTuple):
    """Class that represents the measurement information.

    Attributes
    ----------
        display_name (str): The measurement display name for client to display to user.

        version (str): The measurement version that helps to
        maintain versions of a measurement in future.

        ui_file_paths (list): Absolute paths of the UI file(s) linked to the measurement.

    """

    display_name: str
    version: str
    ui_file_paths: List[Path]


class ServiceInfo(NamedTuple):
    """Class that represents the service information.

    Attributes
    ----------
        service_class (str): Service class that the measurement belongs to.
        Measurements under same service class expected to perform same logic.
        For e.g., different version of measurement can come under same service class.


        description_url (str): Description URL of the measurement.

        provided_interfaces (List[str]): List of interfaces the service provides.
        For e.g., ni.measurementlink.measurement.v2.MeasurementService.
        Defaults to ["ni.measurementlink.measurement.v1.MeasurementService"].

        annotations (Dict[str,str]): Dict that contains extra information of the measurement.
        As default we added a (str) description, (str) collection and a (List[str]) list of tags.
        Feel free to add your own Annotations as needed.

    """

    service_class: str
    description_url: str
    provided_interfaces: List[str] = ["ni.measurementlink.measurement.v1.MeasurementService"]
    annotations: Dict[str, str] = {}


class TypeSpecialization(enum.Enum):
    """Enum that represents the type specializations for measurement parameters."""

    NoType = ""
    Pin = "pin"
    Path = "path"
    Enum = "enum"


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

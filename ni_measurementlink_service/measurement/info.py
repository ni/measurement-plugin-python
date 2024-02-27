"""Measurement service metadata classes and enums."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Dict, List, NamedTuple


class MeasurementInfo(NamedTuple):
    """A named tuple providing information about a measurement."""

    display_name: str
    """The user visible name of the measurement."""

    version: str
    """The current version of the measurement."""

    ui_file_paths: List[Path]
    """Absolute paths to user interface files for the measurement (e.g. ``.measui`` or ``.vi``
    files)."""


class ServiceInfo(NamedTuple):
    """A named tuple providing information about a registered service.

    This class is used with the MeasurementLink discovery service when registering and enumerating
    services.
    """

    service_class: str
    """"The "class" of a service. The value of this field should be unique for a given interface
    in ``provided_interfaces``. In effect, the ``.proto`` service declaration defines the
    interface, and this field defines a class or concrete type of the interface."""

    description_url: str
    """The URL of a web page that provides a description of the service."""

    provided_interfaces: List[str] = ["ni.measurementlink.measurement.v1.MeasurementService"]
    """The service interfaces provided by the service. These are gRPC full names for the service."""

    annotations: Dict[str, str] = {}
    """Represents a set of annotations on the service.
    
    Well-known annotations:

    - Description
       - Key: "ni/service.description"
          - Expected format: string
          - Example: "Measure inrush current with a shorted load and validate results against
            configured limits."
    - Collection
       - Key: "ni/service.collection"
          - Expected format: "." delimited namespace/hierarchy case-insensitive string
          - Example: "CurrentTests.Inrush"
    - Tags
        - Key: "ni/service.tags"
           - Expected format: serialized JSON string of an array of strings
           - Example: "[\"powerup\", \"current\"]"
    """

    display_name: str = ""
    """The service display name for clients to display to users."""


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
    DoubleXYDataArray1D = 111

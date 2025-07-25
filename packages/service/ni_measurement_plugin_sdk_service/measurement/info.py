"""Measurement service metadata classes and enums."""

from __future__ import annotations

import abc
import enum
from pathlib import Path
from typing import Any, NamedTuple
from google.protobuf.message import Message
from google.protobuf import wrappers_pb2
from ni.protobuf.types import waveform_pb2, array_pb2, xydata_pb2
from ni.measurements.data.v1 import data_store_pb2

from ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
)


class MeasurementInfo(NamedTuple):
    """A named tuple providing information about a measurement."""

    display_name: str
    """The user visible name of the measurement."""

    version: str
    """The current version of the measurement."""

    ui_file_paths: list[Path]
    """Absolute paths to user interface files for the measurement (e.g. ``.measui`` or ``.vi``
    files)."""


class ServiceInfo(NamedTuple):
    """A named tuple providing information about a registered service.

    This class is used with the NI Discovery Service when registering and enumerating services.
    """

    service_class: str
    """"The "class" of a service. The value of this field should be unique for all services.
    In effect, the ``.proto`` service declaration defines the interface, and this field
    defines a class or concrete type of the interface."""

    description_url: str
    """The URL of a web page that provides a description of the service."""

    provided_interfaces: list[str] = ["ni.measurementlink.measurement.v1.MeasurementService"]
    """The service interfaces provided by the service. These are gRPC full names for the service."""

    annotations: dict[str, str] = {}
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

    versions: list[str] = []
    """The list of versions associated with this service in
     the form major.minor.build[.revision] (e.g. 1.0.0)."""

    @classmethod
    def _from_grpc(cls, other: discovery_service_pb2.ServiceDescriptor) -> ServiceInfo:
        return ServiceInfo(
            service_class=other.service_class,
            description_url=other.description_url,
            provided_interfaces=list(other.provided_interfaces),
            annotations=dict(other.annotations),
            display_name=other.display_name,
            versions=list(other.versions),
        )


class TypeSpecialization(enum.Enum):
    """Enum that represents the type specializations for measurement parameters."""

    NoType = ""
    Pin = "pin"
    Path = "path"
    Enum = "enum"
    IOResource = "ioresource"


class ABCEnumMeta(abc.ABCMeta, enum.EnumMeta): ...


class ParameterType(abc.ABC, enum.Enum, metaclass=ABCEnumMeta):
    @abc.abstractmethod
    def to_url(self) -> str:
        """Convert the parameter type to a URL."""
        ...

    def to_message(self) -> Message:
        """Convert the parameter type to a message."""
        ...


class DataType(ParameterType):
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

    def to_url(self) -> str:
        if self == DataType.Int32:
            return "type.googleapis.com/google.protobuf.Int32Value"
        elif self == DataType.Int64:
            return "type.googleapis.com/google.protobuf.Int64Value"
        elif self == DataType.UInt32:
            return "type.googleapis.com/google.protobuf.UInt32Value"
        elif self == DataType.UInt64:
            return "type.googleapis.com/google.protobuf.UInt64Value"
        elif self == DataType.Float:
            return "type.googleapis.com/google.protobuf.FloatValue"
        elif self == DataType.Double:
            return "type.googleapis.com/google.protobuf.DoubleValue"
        elif self == DataType.Boolean:
            return "type.googleapis.com/google.protobuf.BooleanValue"
        elif self == DataType.String:
            return "type.googleapis.com/google.protobuf.StringData"
        elif self == DataType.Pin:
            return "type.googleapis.com/google.protobuf.PinValue"
        elif self == DataType.Path:
            return "type.googleapis.com/google.protobuf.PathValue"
        elif self == DataType.Enum:
            return "type.googleapis.com/google.protobuf.EnumValue"
        elif self == DataType.DoubleXYData:
            return "type.googleapis.com/ni.protobuf.types.DoubleXYData"
        elif self == DataType.IOResource:
            return "type.googleapis.com/ni.measurementlink.iodiscovery.v1.IOResource"
        elif self == DataType.Double2DArray:
            return "type.googleapis.com/ni.protobuf.types.Double2DArray"
        elif self == DataType.String2DArray:
            return "type.googleapis.com/ni.protobuf.types.String2DArray"
        else:
            raise ValueError(f"Unsupported DataType: {self}")

    def to_message(self, value: Any) -> Message:
        """Convert the DataType to a protobuf message."""
        if self == DataType.Int32:
            return wrappers_pb2.Int32Value(value=value)
        elif self == DataType.Int64:
            return wrappers_pb2.Int64Value(value=value)
        elif self == DataType.UInt32:
            return wrappers_pb2.UInt32Value(value=value)
        elif self == DataType.UInt64:
            return wrappers_pb2.UInt64Value(value=value)
        elif self == DataType.Float:
            return wrappers_pb2.FloatValue(value=value)
        elif self == DataType.Double:
            return wrappers_pb2.DoubleValue(value=value)
        elif self == DataType.Boolean:
            return wrappers_pb2.BoolValue(value=value)
        elif self == DataType.String:
            return wrappers_pb2.StringValue(value=value)
        else:
            raise ValueError(f"Unsupported DataType: {self}")


class MonikerType(ParameterType):
    """Enum that represents the moniker types for measurement inputs/outputs."""

    ScalarData = enum.auto()
    ScalarArray = enum.auto()
    ConditionSet = enum.auto()
    String2DArray = enum.auto()
    Double2DArray = enum.auto()
    DoubleXYData = enum.auto()
    DoubleAnalogWaveform = enum.auto()

    def to_url(self) -> str:
        if self == MonikerType.ScalarData:
            return "type.googleapis.com/ni.measurements.data.v1.ScalarData"
        elif self == MonikerType.ScalarArray:
            return "type.googleapis.com/ni.measurements.data.v1.ScalarArray"
        elif self == MonikerType.ConditionSet:
            return "type.googleapis.com/ni.measurements.data.v1.ConditionSet"
        elif self == MonikerType.String2DArray:
            return "type.googleapis.com/ni.protobuf.types.String2DArray"
        elif self == MonikerType.Double2DArray:
            return "type.googleapis.com/ni.protobuf.types.Double2DArray"
        elif self == MonikerType.DoubleXYData:
            return "type.googleapis.com/ni.protobuf.types.DoubleXYData"
        elif self == MonikerType.DoubleAnalogWaveform:
            return "type.googleapis.com/ni.protobuf.types.DoubleAnalogWaveform"
        else:
            raise ValueError(f"Unsupported MonikerType: {self}")

    def to_message(self) -> Message:
        if self == MonikerType.ScalarData:
            return data_store_pb2.ScalarData()
        elif self == MonikerType.ScalarArray:
            return data_store_pb2.ScalarArray()
        elif self == MonikerType.ConditionSet:
            return data_store_pb2.ConditionSet()
        elif self == MonikerType.String2DArray:
            return array_pb2.String2DArray()
        elif self == MonikerType.Double2DArray:
            return array_pb2.Double2DArray()
        elif self == MonikerType.DoubleXYData:
            return xydata_pb2.DoubleXYData()
        elif self == MonikerType.DoubleAnalogWaveform:
            return waveform_pb2.DoubleAnalogWaveform()
        else:
            raise ValueError(f"Unsupported MonikerType: {self}")

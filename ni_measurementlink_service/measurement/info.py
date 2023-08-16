"""Contains classes and enums to represent measurement metadata."""
from __future__ import annotations

import enum
from pathlib import Path
from typing import Dict, List, NamedTuple

from google.protobuf import type_pb2


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

    Int32 = (0,)
    Int64 = (1,)
    UInt32 = (2,)
    UInt64 = (3,)
    Float = (4,)
    Double = (5,)
    Boolean = (6,)
    String = (7,)
    Pin = (8,)
    Path = (9,)
    Enum = (10,)

    Int32Array1D = (100,)
    Int64Array1D = (101,)
    UInt32Array1D = (102,)
    UInt64Array1D = (103,)
    FloatArray1D = (104,)
    DoubleArray1D = (105,)
    BooleanArray1D = (106,)
    StringArray1D = (107,)
    PinArray1D = (108,)
    PathArray1D = (109,)
    EnumArray1D = (110,)


class DataTypeInfo(NamedTuple):
    """Class that represents the information for each of the DataType enum values.

    Attributes
    ----------
        grpc_field_type (type_pb2.Field.Kind): Field.Kind associated with the DataType

        repeated (bool): Whether the DataType is a repeated field

        type_specialization (TypeSpecialization): Specific type when value_type
        can have more than one use

    """

    grpc_field_type: type_pb2.Field.Kind
    repeated: bool
    type_specialization: TypeSpecialization = TypeSpecialization.NoType


Int32TypeInfo = DataTypeInfo(type_pb2.Field.TYPE_INT32, False)
Int64TypeInfo = DataTypeInfo(type_pb2.Field.TYPE_INT64, False)
UInt32TypeInfo = DataTypeInfo(type_pb2.Field.TYPE_UINT32, False)
UInt64TypeInfo = DataTypeInfo(type_pb2.Field.TYPE_UINT64, False)
FloatTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_FLOAT, False)
DoubleTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_DOUBLE, False)
BooleanTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_BOOL, False)
StringTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, False)
PinTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, False, TypeSpecialization.Pin)
PathTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, False, TypeSpecialization.Path)
EnumTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_ENUM, False, TypeSpecialization.Enum)

Int32Array1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_INT32, True)
Int64Array1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_INT64, True)
UInt32Array1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_UINT32, True)
UInt64Array1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_UINT64, True)
FloatArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_FLOAT, True)
DoubleArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_DOUBLE, True)
BooleanArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_BOOL, True)
StringArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, True)
PinArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, True, TypeSpecialization.Pin)
PathArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_STRING, True, TypeSpecialization.Path)
EnumArray1DTypeInfo = DataTypeInfo(type_pb2.Field.TYPE_ENUM, True, TypeSpecialization.Enum)


class DataTypeInfoLookup:
    _DATATYPE_TO_DATATYPEINFO_LOOKUP = {
        DataType.Int32: Int32TypeInfo,
        DataType.Int64: Int64TypeInfo,
        DataType.UInt32: UInt32TypeInfo,
        DataType.UInt64: UInt64TypeInfo,
        DataType.Float: FloatTypeInfo,
        DataType.Double: DoubleTypeInfo,
        DataType.Boolean: BooleanTypeInfo,
        DataType.String: StringTypeInfo,
        DataType.Pin: PinTypeInfo,
        DataType.Path: PathTypeInfo,
        DataType.Enum: EnumTypeInfo,
        DataType.Int32Array1D: Int32Array1DTypeInfo,
        DataType.Int64Array1D: Int64Array1DTypeInfo,
        DataType.UInt32Array1D: UInt32Array1DTypeInfo,
        DataType.UInt64Array1D: UInt64Array1DTypeInfo,
        DataType.FloatArray1D: FloatArray1DTypeInfo,
        DataType.DoubleArray1D: DoubleArray1DTypeInfo,
        DataType.BooleanArray1D: BooleanArray1DTypeInfo,
        DataType.StringArray1D: StringArray1DTypeInfo,
        DataType.PinArray1D: PinArray1DTypeInfo,
        DataType.PathArray1D: PathArray1DTypeInfo,
        DataType.EnumArray1D: EnumArray1DTypeInfo,
    }

    @staticmethod
    def get_type_info(data_type: DataType) -> DataTypeInfo:
        if data_type not in DataTypeInfoLookup._DATATYPE_TO_DATATYPEINFO_LOOKUP:
            raise Exception(f"Data type information not found '{data_type}'")
        data_type_info = DataTypeInfoLookup._DATATYPE_TO_DATATYPEINFO_LOOKUP[data_type]
        return data_type_info

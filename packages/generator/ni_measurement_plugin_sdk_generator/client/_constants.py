"""Measurement Plug-In Client generator constants."""

from google.protobuf.type_pb2 import Field

V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

INVALID_CHARS = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n"

XY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import DoubleXYData"
PATH_IMPORT = "from pathlib import Path"

PROTO_DATATYPE_TO_PYTYPE_LOOKUP = {
    Field.TYPE_INT32: int,
    Field.TYPE_INT64: int,
    Field.TYPE_UINT32: int,
    Field.TYPE_UINT64: int,
    Field.TYPE_SINT32: int,
    Field.TYPE_SINT64: int,
    Field.TYPE_FIXED32: int,
    Field.TYPE_FIXED64: int,
    Field.TYPE_SFIXED32: int,
    Field.TYPE_SFIXED64: int,
    Field.TYPE_FLOAT: float,
    Field.TYPE_DOUBLE: float,
    Field.TYPE_BOOL: bool,
    Field.TYPE_STRING: str,
    Field.TYPE_ENUM: int,
    Field.TYPE_MESSAGE: str,
}

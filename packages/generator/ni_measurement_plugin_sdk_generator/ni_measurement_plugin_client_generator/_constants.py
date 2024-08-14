"""Measurement plug-in client generator constants."""

from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import (
    DoubleXYData,
)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

_INVALID_CHARS = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n"

_XY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import DoubleXYData"
_PATH_IMPORT = "from pathlib import Path"

_DEFAULT_IMPORT_TYPE = "In-Built"
_CUSTOM_IMPORT_TYPE = "Custom"
_IMPORT_MODULES = {}

_PROTO_DATATYPE_TO_PYTYPE_LOOKUP = {
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
    Field.TYPE_MESSAGE: DoubleXYData,
}

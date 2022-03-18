import enum
from typing import NamedTuple
import google.protobuf.type_pb2 as type_pb2


class MeasurementInfo(NamedTuple):
    display_name: str = None
    version: str = None
    measurement_type: str = None
    product_type: str = None
    ui_file_path: str = None
    ui_file_type: str = None


class ServiceInfo(NamedTuple):
    service_class: str
    service_id: str
    description_url: str


class DataType(enum.Enum):
    Int32 = (type_pb2.Field.TYPE_INT32, False)
    Int64 = (type_pb2.Field.TYPE_INT64, False)
    UInt32 = (type_pb2.Field.TYPE_UINT32, False)
    UInt64 = (type_pb2.Field.TYPE_UINT64, False)
    Float = (type_pb2.Field.TYPE_FLOAT, False)
    Double = (type_pb2.Field.TYPE_DOUBLE, False)
    Boolean = (type_pb2.Field.TYPE_BOOL, False)
    String = (type_pb2.Field.TYPE_STRING, False)

    Int32Array1D = (type_pb2.Field.TYPE_INT32, True)
    Int64Array1D = (type_pb2.Field.TYPE_INT64, True)
    UInt32Array1D = (type_pb2.Field.TYPE_UINT32, True)
    UInt64Array1D = (type_pb2.Field.TYPE_UINT64, True)
    FloatArray1D = (type_pb2.Field.TYPE_FLOAT, True)
    DoubleArray1D = (type_pb2.Field.TYPE_DOUBLE, True)

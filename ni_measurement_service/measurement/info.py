"""Contains classes and enums to represent measurement metadata."""

import enum
from typing import NamedTuple

from google.protobuf import type_pb2


class UIFileType(enum.Enum):
    """Enum that represents the supported UI Types."""

    MeasurementUI = "ni_measui://"
    LabVIEW = "ni_vi://"


class MeasurementInfo(NamedTuple):
    """Class that represents the measurement information.

    Attributes
    ----------
        display_name (str): The measurement display name for client to display to user.

        version (str): The measurement version that helps to
        maintain versions of a measurement in future.

        measurement_type (str): Represents category of measurement for the ProductType,
        e.g. AC or DC measurements.

        product_type (str): Represents type of the DUT,
        e.g. ADC, LDO.

        ui_file_path (str): Path of the UI file linked to the measurement.

        ui_file_type (UIFileType): Type of the linked UI file.

    """

    display_name: str
    version: str
    measurement_type: str
    product_type: str
    ui_file_path: str
    ui_file_type: UIFileType


class ServiceInfo(NamedTuple):
    """Class the represents the service information.

    Attributes
    ----------
        service_class (str): Service class that the measurement belongs to.
        Measurements under same service class expected to perform same logic.
        For e.g., different version of measurement can come under same service class.

        service_id (str): Unique service of the measurement. Should be an Unique GUID.

        description_url (str): Description URL of the measurement.

    """

    service_class: str
    service_id: str
    description_url: str


class DataType(enum.Enum):
    """Enum that represents the supported data types."""

    Int32 = (type_pb2.Field.TYPE_INT32, False)
    Int64 = (type_pb2.Field.TYPE_INT64, False)
    UInt32 = (type_pb2.Field.TYPE_UINT32, False)
    UInt64 = (type_pb2.Field.TYPE_UINT64, False)
    Float = (type_pb2.Field.TYPE_FLOAT, False)
    Double = (type_pb2.Field.TYPE_DOUBLE, False)
    Boolean = (type_pb2.Field.TYPE_BOOL, False)
    String = (type_pb2.Field.TYPE_STRING, False)

    DoubleArray1D = (type_pb2.Field.TYPE_DOUBLE, True)

import enum


class MonikerType(enum.Enum):
    """Enum that represents the moniker types for measurement inputs/outputs."""

    ScalarData = enum.auto()
    ScalarArray = enum.auto()
    Condition = enum.auto()
    ConditionArray = enum.auto()
    String2DArray = enum.auto()
    Double2DArray = enum.auto()
    DoubleXYData = enum.auto()
    DoubleAnalogWaveform = enum.auto()

    def to_url(self) -> str:
        if self == MonikerType.ScalarData:
            return "type.googleapis.com/ni.measurements.data.v1.ScalarData"
        elif self == MonikerType.ScalarArray:
            return "type.googleapis.com/ni.measurements.data.v1.ScalarArray"
        elif self == MonikerType.Condition:
            return "type.googleapis.com/ni.measurements.data.v1.Condition"
        elif self == MonikerType.ConditionArray:
            return "type.googleapis.com/ni.measurements.data.v1.ConditionArray"
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

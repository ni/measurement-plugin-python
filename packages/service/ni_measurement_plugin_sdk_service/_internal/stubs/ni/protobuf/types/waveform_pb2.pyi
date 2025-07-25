"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
---------------------------------------------------------------------
---------------------------------------------------------------------
"""

import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.precision_timestamp_pb2 as ni_protobuf_types_precision_timestamp_pb2
import typing

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class DoubleAnalogWaveform(google.protobuf.message.Message):
    """Detailed documentation for waveform attributes:
    A waveform attribute is metadata attached to a waveform.
    It is represented in this message as a map associating the name of the attribute with the value described by WaveformAttributeValue.
    The NI-DAQmx driver sets the following string attributes:
    NI_ChannelName: the name of the virtual channel producing the waveform.
    NI_LineNames: the name of the digital line in the waveform.
    NI_UnitDescription: the units of measure for the waveform.
    NI_dBReference: the reference value to use when converting measurement levels to decibel.
    For additional information on waveform attributes, please visit https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/functions/get-waveform-attribute.html

    An analog waveform, which encapsulates analog data as doubles and timing information.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class AttributesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___WaveformAttributeValue: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___WaveformAttributeValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal["key", b"key", "value", b"value"]) -> None: ...

    T0_FIELD_NUMBER: builtins.int
    DT_FIELD_NUMBER: builtins.int
    Y_DATA_FIELD_NUMBER: builtins.int
    ATTRIBUTES_FIELD_NUMBER: builtins.int
    dt: builtins.float
    """The time interval in seconds between data points in the waveform."""
    @property
    def t0(self) -> ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp:
        """The time of the first sample in y_data."""

    @property
    def y_data(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.float]:
        """The data values of the waveform."""

    @property
    def attributes(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___WaveformAttributeValue]:
        """The names and values of all waveform attributes.
        See the comment at near the top of this file for more details.
        """

    def __init__(
        self,
        *,
        t0: ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp | None = ...,
        dt: builtins.float = ...,
        y_data: collections.abc.Iterable[builtins.float] | None = ...,
        attributes: collections.abc.Mapping[builtins.str, global___WaveformAttributeValue] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["t0", b"t0"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["attributes", b"attributes", "dt", b"dt", "t0", b"t0", "y_data", b"y_data"]) -> None: ...

global___DoubleAnalogWaveform = DoubleAnalogWaveform

@typing.final
class I16AnalogWaveform(google.protobuf.message.Message):
    """An analog waveform, which encapsulates analog data as 16 bit integers and timing information."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class AttributesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___WaveformAttributeValue: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___WaveformAttributeValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal["key", b"key", "value", b"value"]) -> None: ...

    T0_FIELD_NUMBER: builtins.int
    DT_FIELD_NUMBER: builtins.int
    Y_DATA_FIELD_NUMBER: builtins.int
    ATTRIBUTES_FIELD_NUMBER: builtins.int
    SCALE_FIELD_NUMBER: builtins.int
    dt: builtins.float
    """The time interval in seconds between data points in the waveform."""
    @property
    def t0(self) -> ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp:
        """The time of the first sample in y_data."""

    @property
    def y_data(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]:
        """The data values of the waveform."""

    @property
    def attributes(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___WaveformAttributeValue]:
        """The names and values of all waveform attributes.
        See the comment at near the top of this file for more details.
        """

    @property
    def scale(self) -> global___Scale:
        """Optional scaling information which can be used to convert unscaled data represented by this waveform to scaled data."""

    def __init__(
        self,
        *,
        t0: ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp | None = ...,
        dt: builtins.float = ...,
        y_data: collections.abc.Iterable[builtins.int] | None = ...,
        attributes: collections.abc.Mapping[builtins.str, global___WaveformAttributeValue] | None = ...,
        scale: global___Scale | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["scale", b"scale", "t0", b"t0"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["attributes", b"attributes", "dt", b"dt", "scale", b"scale", "t0", b"t0", "y_data", b"y_data"]) -> None: ...

global___I16AnalogWaveform = I16AnalogWaveform

@typing.final
class DoubleComplexWaveform(google.protobuf.message.Message):
    """A complex waveform, which encapsulates complex data as doubles and timing information."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class AttributesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___WaveformAttributeValue: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___WaveformAttributeValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal["key", b"key", "value", b"value"]) -> None: ...

    T0_FIELD_NUMBER: builtins.int
    DT_FIELD_NUMBER: builtins.int
    Y_DATA_FIELD_NUMBER: builtins.int
    ATTRIBUTES_FIELD_NUMBER: builtins.int
    dt: builtins.float
    """The time interval in seconds between data points in the waveform."""
    @property
    def t0(self) -> ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp:
        """The time of the first sample in y_data."""

    @property
    def y_data(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.float]:
        """The data values of the waveform.
        Real and imaginary parts interleaved.  Example: [1.0+2.0j, 3.0+4.0j] is represented as [1.0, 2.0, 3.0, 4.0].
        """

    @property
    def attributes(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___WaveformAttributeValue]:
        """The names and values of all waveform attributes.
        See the comment at near the top of this file for more details.
        """

    def __init__(
        self,
        *,
        t0: ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp | None = ...,
        dt: builtins.float = ...,
        y_data: collections.abc.Iterable[builtins.float] | None = ...,
        attributes: collections.abc.Mapping[builtins.str, global___WaveformAttributeValue] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["t0", b"t0"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["attributes", b"attributes", "dt", b"dt", "t0", b"t0", "y_data", b"y_data"]) -> None: ...

global___DoubleComplexWaveform = DoubleComplexWaveform

@typing.final
class I16ComplexWaveform(google.protobuf.message.Message):
    """A complex waveform, which encapsulates complex data as 16 bit integers and timing information."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class AttributesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___WaveformAttributeValue: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___WaveformAttributeValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal["key", b"key", "value", b"value"]) -> None: ...

    T0_FIELD_NUMBER: builtins.int
    DT_FIELD_NUMBER: builtins.int
    Y_DATA_FIELD_NUMBER: builtins.int
    ATTRIBUTES_FIELD_NUMBER: builtins.int
    SCALE_FIELD_NUMBER: builtins.int
    dt: builtins.float
    """The time interval in seconds between data points in the waveform."""
    @property
    def t0(self) -> ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp:
        """The time of the first sample in y_data."""

    @property
    def y_data(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]:
        """The data values of the waveform.
        Real and imaginary parts interleaved. Example: [1+2j, 3+4j] is represented as [1, 2, 3, 4].
        """

    @property
    def attributes(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___WaveformAttributeValue]:
        """The names and values of all waveform attributes.
        See the comment at near the top of this file for more details.
        """

    @property
    def scale(self) -> global___Scale:
        """Optional scaling information which can be used to convert unscaled data represented by this waveform to scaled data."""

    def __init__(
        self,
        *,
        t0: ni_protobuf_types_precision_timestamp_pb2.PrecisionTimestamp | None = ...,
        dt: builtins.float = ...,
        y_data: collections.abc.Iterable[builtins.int] | None = ...,
        attributes: collections.abc.Mapping[builtins.str, global___WaveformAttributeValue] | None = ...,
        scale: global___Scale | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["scale", b"scale", "t0", b"t0"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["attributes", b"attributes", "dt", b"dt", "scale", b"scale", "t0", b"t0", "y_data", b"y_data"]) -> None: ...

global___I16ComplexWaveform = I16ComplexWaveform

@typing.final
class DoubleSpectrum(google.protobuf.message.Message):
    """A frequency spectrum, which encapsulates analog data and frequency information."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing.final
    class AttributesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___WaveformAttributeValue: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___WaveformAttributeValue | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing.Literal["key", b"key", "value", b"value"]) -> None: ...

    START_FREQUENCY_FIELD_NUMBER: builtins.int
    FREQUENCY_INCREMENT_FIELD_NUMBER: builtins.int
    DATA_FIELD_NUMBER: builtins.int
    ATTRIBUTES_FIELD_NUMBER: builtins.int
    start_frequency: builtins.float
    """The start frequency of the spectrum."""
    frequency_increment: builtins.float
    """The frequency increment of the spectrum."""
    @property
    def data(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.float]:
        """The data values of the spectrum."""

    @property
    def attributes(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___WaveformAttributeValue]:
        """The names and values of all waveform attributes.
        See the comment at near the top of this file for more details.
        """

    def __init__(
        self,
        *,
        start_frequency: builtins.float = ...,
        frequency_increment: builtins.float = ...,
        data: collections.abc.Iterable[builtins.float] | None = ...,
        attributes: collections.abc.Mapping[builtins.str, global___WaveformAttributeValue] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["attributes", b"attributes", "data", b"data", "frequency_increment", b"frequency_increment", "start_frequency", b"start_frequency"]) -> None: ...

global___DoubleSpectrum = DoubleSpectrum

@typing.final
class WaveformAttributeValue(google.protobuf.message.Message):
    """Waveform Attribute Value"""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    BOOL_VALUE_FIELD_NUMBER: builtins.int
    INTEGER_VALUE_FIELD_NUMBER: builtins.int
    DOUBLE_VALUE_FIELD_NUMBER: builtins.int
    STRING_VALUE_FIELD_NUMBER: builtins.int
    bool_value: builtins.bool
    """Represents a bool attribute."""
    integer_value: builtins.int
    """Represents an integer attribute."""
    double_value: builtins.float
    """Represents a double attribute."""
    string_value: builtins.str
    """Represents a string attribute."""
    def __init__(
        self,
        *,
        bool_value: builtins.bool = ...,
        integer_value: builtins.int = ...,
        double_value: builtins.float = ...,
        string_value: builtins.str = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["attribute", b"attribute", "bool_value", b"bool_value", "double_value", b"double_value", "integer_value", b"integer_value", "string_value", b"string_value"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["attribute", b"attribute", "bool_value", b"bool_value", "double_value", b"double_value", "integer_value", b"integer_value", "string_value", b"string_value"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["attribute", b"attribute"]) -> typing.Literal["bool_value", "integer_value", "double_value", "string_value"] | None: ...

global___WaveformAttributeValue = WaveformAttributeValue

@typing.final
class Scale(google.protobuf.message.Message):
    """Scaling information which can be used to convert unscaled data represented by this waveform to scaled data."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    LINEAR_SCALE_FIELD_NUMBER: builtins.int
    @property
    def linear_scale(self) -> global___LinearScale: ...
    def __init__(
        self,
        *,
        linear_scale: global___LinearScale | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["linear_scale", b"linear_scale", "mode", b"mode"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["linear_scale", b"linear_scale", "mode", b"mode"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["mode", b"mode"]) -> typing.Literal["linear_scale"] | None: ...

global___Scale = Scale

@typing.final
class LinearScale(google.protobuf.message.Message):
    """LinearScale datatype."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    GAIN_FIELD_NUMBER: builtins.int
    OFFSET_FIELD_NUMBER: builtins.int
    gain: builtins.float
    """The gain of the linear scale"""
    offset: builtins.float
    """The offset of the linear scale"""
    def __init__(
        self,
        *,
        gain: builtins.float = ...,
        offset: builtins.float = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["gain", b"gain", "offset", b"offset"]) -> None: ...

global___LinearScale = LinearScale

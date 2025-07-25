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
import ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.waveform_pb2 as ni_protobuf_types_waveform_pb2
import typing

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class DoubleAnalogWaveformArrayValue(google.protobuf.message.Message):
    """Wrappers for common waveform message types. These types are useful
    for embedding in the google.protobuf.Any type or in oneof fields.
    Their use outside of these scenarios is discouraged.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WAVEFORMS_FIELD_NUMBER: builtins.int
    @property
    def waveforms(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[ni_protobuf_types_waveform_pb2.DoubleAnalogWaveform]: ...
    def __init__(
        self,
        *,
        waveforms: collections.abc.Iterable[ni_protobuf_types_waveform_pb2.DoubleAnalogWaveform] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["waveforms", b"waveforms"]) -> None: ...

global___DoubleAnalogWaveformArrayValue = DoubleAnalogWaveformArrayValue

@typing.final
class I16AnalogWaveformArrayValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WAVEFORMS_FIELD_NUMBER: builtins.int
    @property
    def waveforms(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[ni_protobuf_types_waveform_pb2.I16AnalogWaveform]: ...
    def __init__(
        self,
        *,
        waveforms: collections.abc.Iterable[ni_protobuf_types_waveform_pb2.I16AnalogWaveform] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["waveforms", b"waveforms"]) -> None: ...

global___I16AnalogWaveformArrayValue = I16AnalogWaveformArrayValue

@typing.final
class DoubleComplexWaveformArrayValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WAVEFORMS_FIELD_NUMBER: builtins.int
    @property
    def waveforms(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[ni_protobuf_types_waveform_pb2.DoubleComplexWaveform]: ...
    def __init__(
        self,
        *,
        waveforms: collections.abc.Iterable[ni_protobuf_types_waveform_pb2.DoubleComplexWaveform] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["waveforms", b"waveforms"]) -> None: ...

global___DoubleComplexWaveformArrayValue = DoubleComplexWaveformArrayValue

@typing.final
class I16ComplexWaveformArrayValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WAVEFORMS_FIELD_NUMBER: builtins.int
    @property
    def waveforms(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[ni_protobuf_types_waveform_pb2.I16ComplexWaveform]: ...
    def __init__(
        self,
        *,
        waveforms: collections.abc.Iterable[ni_protobuf_types_waveform_pb2.I16ComplexWaveform] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["waveforms", b"waveforms"]) -> None: ...

global___I16ComplexWaveformArrayValue = I16ComplexWaveformArrayValue

@typing.final
class DoubleSpectrumArrayValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    WAVEFORMS_FIELD_NUMBER: builtins.int
    @property
    def waveforms(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[ni_protobuf_types_waveform_pb2.DoubleSpectrum]: ...
    def __init__(
        self,
        *,
        waveforms: collections.abc.Iterable[ni_protobuf_types_waveform_pb2.DoubleSpectrum] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["waveforms", b"waveforms"]) -> None: ...

global___DoubleSpectrumArrayValue = DoubleSpectrumArrayValue

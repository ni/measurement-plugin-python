"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class Configurations(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PIN_NAMES_FIELD_NUMBER: builtins.int
    MULTI_SESSION_FIELD_NUMBER: builtins.int
    @property
    def pin_names(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    multi_session: builtins.bool
    def __init__(
        self,
        *,
        pin_names: collections.abc.Iterable[builtins.str] | None = ...,
        multi_session: builtins.bool = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["multi_session", b"multi_session", "pin_names", b"pin_names"]) -> None: ...

global___Configurations = Configurations

@typing_extensions.final
class Outputs(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SESSION_NAMES_FIELD_NUMBER: builtins.int
    RESOURCE_NAMES_FIELD_NUMBER: builtins.int
    CHANNEL_LISTS_FIELD_NUMBER: builtins.int
    CONNECTED_CHANNELS_FIELD_NUMBER: builtins.int
    SIGNALS_OUT_OF_RANGE_FIELD_NUMBER: builtins.int
    ABSOLUTE_RESOLUTIONS_FIELD_NUMBER: builtins.int
    @property
    def session_names(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    @property
    def resource_names(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    @property
    def channel_lists(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    @property
    def connected_channels(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.str]: ...
    @property
    def signals_out_of_range(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.bool]: ...
    @property
    def absolute_resolutions(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.float]: ...
    def __init__(
        self,
        *,
        session_names: collections.abc.Iterable[builtins.str] | None = ...,
        resource_names: collections.abc.Iterable[builtins.str] | None = ...,
        channel_lists: collections.abc.Iterable[builtins.str] | None = ...,
        connected_channels: collections.abc.Iterable[builtins.str] | None = ...,
        signals_out_of_range: collections.abc.Iterable[builtins.bool] | None = ...,
        absolute_resolutions: collections.abc.Iterable[builtins.float] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["absolute_resolutions", b"absolute_resolutions", "channel_lists", b"channel_lists", "connected_channels", b"connected_channels", "resource_names", b"resource_names", "session_names", b"session_names", "signals_out_of_range", b"signals_out_of_range"]) -> None: ...

global___Outputs = Outputs

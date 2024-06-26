"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import typing

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Configurations(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    TIME_IN_SECONDS_FIELD_NUMBER: builtins.int
    time_in_seconds: builtins.float
    def __init__(
        self,
        *,
        time_in_seconds: builtins.float = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["time_in_seconds", b"time_in_seconds"]) -> None: ...

global___Configurations = Configurations

@typing.final
class Outputs(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ELAPSED_TIME_IN_SECONDS_FIELD_NUMBER: builtins.int
    RANDOM_NUMBERS_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    elapsed_time_in_seconds: builtins.float
    status: builtins.str
    @property
    def random_numbers(self) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.float]: ...
    def __init__(
        self,
        *,
        elapsed_time_in_seconds: builtins.float = ...,
        random_numbers: collections.abc.Iterable[builtins.float] | None = ...,
        status: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["elapsed_time_in_seconds", b"elapsed_time_in_seconds", "random_numbers", b"random_numbers", "status", b"status"]) -> None: ...

global___Outputs = Outputs

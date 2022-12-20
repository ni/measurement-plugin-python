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
class PinMapContext(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PIN_MAP_ID_FIELD_NUMBER: builtins.int
    SITES_FIELD_NUMBER: builtins.int
    pin_map_id: builtins.str
    """Required. The resource id of the pin map in the Pin Map service that should be used for the call."""
    @property
    def sites(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[builtins.int]:
        """Optional. List of site numbers being used for the call. If unspecified, use all sites in the pin map."""
    def __init__(
        self,
        *,
        pin_map_id: builtins.str = ...,
        sites: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing_extensions.Literal["pin_map_id", b"pin_map_id", "sites", b"sites"]
    ) -> None: ...

global___PinMapContext = PinMapContext

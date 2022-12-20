"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
---------------------------------------------------------------------
---------------------------------------------------------------------
"""
import builtins
import collections.abc
import google.protobuf.any_pb2
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.type_pb2
import ni.measurementlink.pin_map_context_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class GetMetadataRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___GetMetadataRequest = GetMetadataRequest

@typing_extensions.final
class GetMetadataResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    MEASUREMENT_DETAILS_FIELD_NUMBER: builtins.int
    MEASUREMENT_SIGNATURE_FIELD_NUMBER: builtins.int
    USER_INTERFACE_DETAILS_FIELD_NUMBER: builtins.int
    @property
    def measurement_details(self) -> global___MeasurementDetails:
        """Required. Specifies basic information about the measurement."""
    @property
    def measurement_signature(self) -> global___MeasurementSignature:
        """Required. Specifies the signature of the measurement."""
    @property
    def user_interface_details(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UserInterfaceDetails
    ]:
        """Optional. Specifies the user interfaces available for use with the measurement, if any."""
    def __init__(
        self,
        *,
        measurement_details: global___MeasurementDetails | None = ...,
        measurement_signature: global___MeasurementSignature | None = ...,
        user_interface_details: collections.abc.Iterable[global___UserInterfaceDetails]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing_extensions.Literal[
            "measurement_details",
            b"measurement_details",
            "measurement_signature",
            b"measurement_signature",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "measurement_details",
            b"measurement_details",
            "measurement_signature",
            b"measurement_signature",
            "user_interface_details",
            b"user_interface_details",
        ],
    ) -> None: ...

global___GetMetadataResponse = GetMetadataResponse

@typing_extensions.final
class MeasureRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    CONFIGURATION_PARAMETERS_FIELD_NUMBER: builtins.int
    PIN_MAP_CONTEXT_FIELD_NUMBER: builtins.int
    @property
    def configuration_parameters(self) -> google.protobuf.any_pb2.Any:
        """Required. Specifies the configuration to be used for the measurement. Each measurement will define its own set
        of required and optional parameters and generate errors as appropriate if the configuration does not conform
        to valid input ranges.
        """
    @property
    def pin_map_context(self) -> ni.measurementlink.pin_map_context_pb2.PinMapContext:
        """Optional. Specifies the pin map context for the measurement, if any. This field is optional in that callers
        may not always have a pin map context available to include in the request message. Each measurement will
        define if a valid pin map context is required in order to run or not and generate errors appropriately.
        """
    def __init__(
        self,
        *,
        configuration_parameters: google.protobuf.any_pb2.Any | None = ...,
        pin_map_context: ni.measurementlink.pin_map_context_pb2.PinMapContext | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing_extensions.Literal[
            "configuration_parameters",
            b"configuration_parameters",
            "pin_map_context",
            b"pin_map_context",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "configuration_parameters",
            b"configuration_parameters",
            "pin_map_context",
            b"pin_map_context",
        ],
    ) -> None: ...

global___MeasureRequest = MeasureRequest

@typing_extensions.final
class MeasureResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    OUTPUTS_FIELD_NUMBER: builtins.int
    @property
    def outputs(self) -> google.protobuf.any_pb2.Any:
        """Required. Includes the output results from running the measurement. This field is required in that all measurements
        should return a valid output message even if it is just an empty message with no fields. Each measurement will define
        which of its output fields are required and which are optional based on the configuration for the measurement.
        """
    def __init__(
        self,
        *,
        outputs: google.protobuf.any_pb2.Any | None = ...,
    ) -> None: ...
    def HasField(
        self, field_name: typing_extensions.Literal["outputs", b"outputs"]
    ) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["outputs", b"outputs"]) -> None: ...

global___MeasureResponse = MeasureResponse

@typing_extensions.final
class MeasurementDetails(google.protobuf.message.Message):
    """Message that contains standard information reported by a measurement."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DISPLAY_NAME_FIELD_NUMBER: builtins.int
    VERSION_FIELD_NUMBER: builtins.int
    display_name: builtins.str
    """Required. The user visible name of the measurement."""
    version: builtins.str
    """Optional. The current version of the measurement."""
    def __init__(
        self,
        *,
        display_name: builtins.str = ...,
        version: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "display_name", b"display_name", "version", b"version"
        ],
    ) -> None: ...

global___MeasurementDetails = MeasurementDetails

@typing_extensions.final
class MeasurementSignature(google.protobuf.message.Message):
    """Message that defines the signature of a measurement."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    CONFIGURATION_PARAMETERS_MESSAGE_TYPE_FIELD_NUMBER: builtins.int
    CONFIGURATION_PARAMETERS_FIELD_NUMBER: builtins.int
    CONFIGURATION_DEFAULTS_FIELD_NUMBER: builtins.int
    OUTPUTS_MESSAGE_TYPE_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    configuration_parameters_message_type: builtins.str
    """Required. The type name of the message used to define the measurement's configuration.
    This is the gRPC full name for the message.
    """
    @property
    def configuration_parameters(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ConfigurationParameter
    ]:
        """Required. Defines the configuration parameters for the measurement."""
    @property
    def configuration_defaults(self) -> google.protobuf.any_pb2.Any:
        """Optional. The default values to use for the configuration parameters. Caller can use these default values
        rather than specifying their own. These values should be supplied using the message type defined by
        configuration_parameters_message_type.
        """
    outputs_message_type: builtins.str
    """Required. The type name of the message used to define the measurement's outputs.
    This is the gRPC full name for the message.
    """
    @property
    def outputs(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Output]:
        """Required. Defines the outputs for the measurement."""
    def __init__(
        self,
        *,
        configuration_parameters_message_type: builtins.str = ...,
        configuration_parameters: collections.abc.Iterable[global___ConfigurationParameter]
        | None = ...,
        configuration_defaults: google.protobuf.any_pb2.Any | None = ...,
        outputs_message_type: builtins.str = ...,
        outputs: collections.abc.Iterable[global___Output] | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing_extensions.Literal["configuration_defaults", b"configuration_defaults"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "configuration_defaults",
            b"configuration_defaults",
            "configuration_parameters",
            b"configuration_parameters",
            "configuration_parameters_message_type",
            b"configuration_parameters_message_type",
            "outputs",
            b"outputs",
            "outputs_message_type",
            b"outputs_message_type",
        ],
    ) -> None: ...

global___MeasurementSignature = MeasurementSignature

@typing_extensions.final
class UserInterfaceDetails(google.protobuf.message.Message):
    """Contains measurement User Interface details."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FILE_URL_FIELD_NUMBER: builtins.int
    file_url: builtins.str
    """Optional. The URL to the file (such as .measui or .vi) providing a user interface for the measurement."""
    def __init__(
        self,
        *,
        file_url: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing_extensions.Literal["file_url", b"file_url"]
    ) -> None: ...

global___UserInterfaceDetails = UserInterfaceDetails

@typing_extensions.final
class ConfigurationParameter(google.protobuf.message.Message):
    """Message that defines a configuration parameter for the measurement."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class AnnotationsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(
            self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]
        ) -> None: ...

    FIELD_NUMBER_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    REPEATED_FIELD_NUMBER: builtins.int
    ANNOTATIONS_FIELD_NUMBER: builtins.int
    field_number: builtins.int
    """Required. The field number for the configuration parameter as defined by the message indicated by
    MethodSignature.configuration_parameters_message_type.
    """
    type: google.protobuf.type_pb2.Field.Kind.ValueType
    """Required. The data type for the configuration parameter."""
    name: builtins.str
    """Required. The name of the configuration parameter. When defining a user interface for the measurement, a control
    that matches this name will be used to supply a value to this configuration parameter.
    """
    repeated: builtins.bool
    """Required. True if this configuration parameter represents repeated data and False if it represents a scalar value."""
    @property
    def annotations(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]:
        """Optional. Represents a set of annotations on the type.
        Well-known annotations:
        - Type specialization. The keys to other annotations will be read based on the value of `ni/type_specialization` annotation.
          - Key: "ni/type_specialization"
          - Common Values: "pin" ...
        - For string parameter with ni/type_specialization annotation equals "pin"
          - Key: "ni/pin.instrument_type"
          - Common Values: "niDCPower", "niScope"...
        """
    def __init__(
        self,
        *,
        field_number: builtins.int = ...,
        type: google.protobuf.type_pb2.Field.Kind.ValueType = ...,
        name: builtins.str = ...,
        repeated: builtins.bool = ...,
        annotations: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "annotations",
            b"annotations",
            "field_number",
            b"field_number",
            "name",
            b"name",
            "repeated",
            b"repeated",
            "type",
            b"type",
        ],
    ) -> None: ...

global___ConfigurationParameter = ConfigurationParameter

@typing_extensions.final
class Output(google.protobuf.message.Message):
    """Message that defines an output of the measurement."""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FIELD_NUMBER_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    REPEATED_FIELD_NUMBER: builtins.int
    field_number: builtins.int
    """Required. The field number for the output as defined by the message indicated by
    MethodSignature.outputs_message_type.
    """
    type: google.protobuf.type_pb2.Field.Kind.ValueType
    """Required. The data type for the output."""
    name: builtins.str
    """Required. The name of the output. When defining a user interface for the measurement, an indicator
    that matches this name will be used to display the value for this output.
    """
    repeated: builtins.bool
    """Required. True if this output represents repeated data and False if it represents a scalar value."""
    def __init__(
        self,
        *,
        field_number: builtins.int = ...,
        type: google.protobuf.type_pb2.Field.Kind.ValueType = ...,
        name: builtins.str = ...,
        repeated: builtins.bool = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "field_number",
            b"field_number",
            "name",
            b"name",
            "repeated",
            b"repeated",
            "type",
            b"type",
        ],
    ) -> None: ...

global___Output = Output

"""Support functions for the Measurement Plug-In Client generator."""

import json
import keyword
import os
import re
import sys
from enum import Enum
from typing import AbstractSet, Any, Dict, Iterable, List, Optional, Tuple, TypeVar

import click
import grpc
from google.protobuf import descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.grpc_servicer import frame_metadata_dict
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    create_file_descriptor,
    deserialize_parameters,
    ParameterMetadata,
)


_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

_INVALID_CHARS = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n"

_XY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import DoubleXYData"
_PATH_IMPORT = "from pathlib import Path"

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
    Field.TYPE_MESSAGE: str,
}

_T = TypeVar("_T")

# List of regex patterns to convert camel case to snake case
_CAMEL_TO_SNAKE_CASE_REGEXES = [
    re.compile("([^_\n])([A-Z][a-z]+)"),
    re.compile("([a-z])([A-Z])"),
    re.compile("([0-9])([^_0-9])"),
    re.compile("([^_0-9])([0-9])"),
]


def get_measurement_service_stub(
    discovery_client: DiscoveryClient,
    channel_pool: GrpcChannelPool,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    """Returns the measurement service stub of the given service class."""
    try:
        service_location = discovery_client.resolve_service(
            _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise click.ClickException(
                f"Could not find any registered measurement with the service class: '{service_class}'."
            )
        else:
            raise
    channel = channel_pool.get_channel(service_location.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def get_all_registered_measurement_service_classes(discovery_client: DiscoveryClient) -> List[str]:
    """Returns the service classes of all the registered measurement services."""
    registered_measurement_services = discovery_client.enumerate_services(
        _V2_MEASUREMENT_SERVICE_INTERFACE
    )
    measurement_service_classes = [
        measurement_service.service_class for measurement_service in registered_measurement_services
    ]
    return measurement_service_classes


def get_configuration_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    service_class: str,
    enum_values_by_type_name: Dict[str, Dict[str, Any]] = {},
) -> Dict[int, ParameterMetadata]:
    """Returns the configuration metadata of the measurement."""
    configuration_parameter_list = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        configuration_parameter_list.append(
            ParameterMetadata.initialize(
                display_name=configuration.name,
                type=configuration.type,
                repeated=configuration.repeated,
                default_value=None,
                annotations=dict(configuration.annotations.items()),
                message_type=configuration.message_type,
                enum_type=_get_enum_type(configuration, enum_values_by_type_name),
            )
        )

    output_parameter_list = []
    for output in metadata.measurement_signature.outputs:
        output_parameter_list.append(
            ParameterMetadata.initialize(
                display_name=output.name,
                type=output.type,
                repeated=output.repeated,
                default_value=None,
                annotations=dict(output.annotations.items()),
                message_type=output.message_type,
                enum_type=_get_enum_type(output, enum_values_by_type_name),
            )
        )

    create_file_descriptor(
        input_metadata=configuration_parameter_list,
        output_metadata=output_parameter_list,
        service_name=service_class,
        pool=descriptor_pool.Default(),
    )
    configuration_metadata = frame_metadata_dict(configuration_parameter_list)
    deserialized_parameters = deserialize_parameters(
        configuration_metadata,
        metadata.measurement_signature.configuration_defaults.value,
        service_class + ".Configurations",
    )

    for k, v in deserialized_parameters.items():
        if issubclass(type(v), Enum):
            default_value = v.value
        elif issubclass(type(v), list):
            default_value = [e.value for e in v if issubclass(type(e), Enum)]
        else:
            default_value = v

        configuration_metadata[k] = configuration_metadata[k]._replace(default_value=default_value)

    return configuration_metadata


def get_output_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    enum_values_by_type_name: Dict[str, Dict[str, Any]] = {},
) -> Dict[int, ParameterMetadata]:
    """Returns the output metadata of the measurement."""
    output_parameter_list = []
    for output in metadata.measurement_signature.outputs:
        output_parameter_list.append(
            ParameterMetadata.initialize(
                display_name=output.name,
                type=output.type,
                repeated=output.repeated,
                default_value=None,
                annotations=dict(output.annotations.items()),
                message_type=output.message_type,
                enum_type=_get_enum_type(output, enum_values_by_type_name),
            )
        )
    output_metadata = frame_metadata_dict(output_parameter_list)
    return output_metadata


def get_configuration_parameters_with_type_and_default_values(
    configuration_metadata: Dict[int, ParameterMetadata],
    built_in_import_modules: List[str],
    enum_values_by_type_name: Dict[str, Dict[str, Any]] = {},
) -> Tuple[str, str]:
    """Returns configuration parameters of the measurement with type and default values."""
    configuration_parameters = []
    parameter_names = []

    for metadata in configuration_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_names.append(parameter_name)

        default_value = metadata.default_value
        parameter_type = _get_python_type_as_str(metadata.type, metadata.repeated)
        if isinstance(default_value, str):
            default_value = f'"{default_value}"'

        # If it's path type, make the value as raw string literal to ignore escape characters.
        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            default_value = f"r{default_value}"
            parameter_type = "Path"
            built_in_import_modules.append(_PATH_IMPORT)

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"
                default_value = metadata.default_value

        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_type = _get_enum_type(metadata, enum_values_by_type_name)
            parameter_type = enum_type.__name__
            if metadata.repeated:
                values = []
                for val in default_value:
                    enum_value = next((e.name for e in enum_type if e.value == val), None)
                    values.append(f"{parameter_type}.{enum_value}")
                concatenated_default_value = ", ".join(values)
                concatenated_default_value = f"[{concatenated_default_value}]"

                parameter_type = f"List[{parameter_type}]"
                default_value = concatenated_default_value
            else:
                enum_value = next((e.name for e in enum_type if e.value == default_value), None)
                default_value = f"{parameter_type}.{enum_value}"

        configuration_parameters.append(f"{parameter_name}: {parameter_type} = {default_value}")

    # Use line separator and spaces to align the parameters appropriately in the generated file.
    configuration_parameters_with_type_and_value = f",{os.linesep}        ".join(
        configuration_parameters
    )
    parameter_names_as_str = ", ".join(parameter_names)

    return (configuration_parameters_with_type_and_value, parameter_names_as_str)


def get_output_parameters_with_type(
    output_metadata: Dict[int, ParameterMetadata],
    built_in_import_modules: List[str],
    custom_import_modules: List[str],
    enum_values_by_type_name: Dict[str, Dict[str, Any]] = {},
) -> str:
    """Returns the output parameters of the measurement with type."""
    output_parameters_with_type = []
    for metadata in output_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_type = _get_python_type_as_str(metadata.type, metadata.repeated)

        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            parameter_type = "Path"
            built_in_import_modules.append(_PATH_IMPORT)

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            parameter_type = "DoubleXYData"
            custom_import_modules.append(_XY_DATA_IMPORT)

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"

        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_type_name = _get_enum_type(metadata, enum_values_by_type_name).__name__
            parameter_type = f"List[{enum_type_name}]" if metadata.repeated else enum_type_name

        output_parameters_with_type.append(f"{parameter_name}: {parameter_type}")

    return f"{os.linesep}    ".join(output_parameters_with_type)


def to_ordered_set(values: Iterable[_T]) -> AbstractSet[_T]:
    """Converts an iterable to an ordered set."""
    return dict.fromkeys(values).keys()


def camel_to_snake_case(camel_case_string: str) -> str:
    """Converts a camelCase string to a snake_case string."""
    partial = camel_case_string
    for regex in _CAMEL_TO_SNAKE_CASE_REGEXES:
        partial = regex.sub(r"\1_\2", partial)

    return partial.lower()


def remove_suffix(string: str) -> str:
    """Removes the suffix from the given string."""
    suffixes = ["_Python", "_LabVIEW"]
    for suffix in suffixes:
        if string.endswith(suffix):
            if sys.version_info >= (3, 9):
                return string.removesuffix(suffix)
            else:
                return string[0 : len(string) - len(suffix)]
    return string


def is_python_identifier(input_string: Optional[str]) -> bool:
    """Validates whether the given string is a valid Python identifier."""
    if input_string is None:
        return False
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return re.fullmatch(pattern, input_string) is not None


def _get_python_identifier(input_string: str) -> str:
    valid_identifier = input_string.lower()
    if not valid_identifier.isidentifier():
        for invalid_char in _INVALID_CHARS:
            valid_identifier = valid_identifier.replace(invalid_char, "_")

    if valid_identifier[0].isdigit() or keyword.iskeyword(valid_identifier):
        valid_identifier = f"_{valid_identifier}"
    return valid_identifier


def _get_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    python_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)

    if python_type is None:
        raise TypeError(f"Invalid data type: '{type}'.")

    if is_array:
        return f"List[{python_type.__name__}]"
    return python_type.__name__


def _get_enum_type(parameter: Any, enum_values_by_type_name: Dict[str, Dict[str, Any]]) -> Any:
    if parameter.type == FieldDescriptorProto.TYPE_ENUM:
        loaded_enum_values = json.loads(parameter.annotations["ni/enum.values"])
        enum_values = dict((key, value) for key, value in loaded_enum_values.items())

        for existing_enum_name, existing_enum_values in enum_values_by_type_name.items():
            if existing_enum_values == enum_values:
                return Enum(existing_enum_name, existing_enum_values)

        new_enum_type_name = _get_enum_class_name(parameter.name)
        enum_values_by_type_name[new_enum_type_name] = enum_values
        return Enum(new_enum_type_name, enum_values)
    return None


def _get_enum_class_name(name: str) -> str:
    class_name = name.title().replace(" ", "")
    invalid_chars = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n_"
    pattern = f"[{re.escape(invalid_chars)}]"
    class_name = re.sub(pattern, "", class_name)
    return class_name + "Enum"

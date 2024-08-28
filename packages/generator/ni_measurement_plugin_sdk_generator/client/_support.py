"""Support functions for the Measurement Plug-In Client generator."""

import keyword
import os
import re
from typing import AbstractSet, Dict, Iterable, List, Tuple, TypeVar

import click
import grpc
from google.protobuf import descriptor_pool
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

from ni_measurement_plugin_sdk_generator.client._constants import (
    INVALID_CHARS,
    PATH_IMPORT,
    PROTO_DATATYPE_TO_PYTYPE_LOOKUP,
    V2_MEASUREMENT_SERVICE_INTERFACE,
    XY_DATA_IMPORT,
)


_T = TypeVar("_T")
CAMEL_TO_SNAKE_CASE_REGEXES = [
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
            V2_MEASUREMENT_SERVICE_INTERFACE, service_class
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise click.ClickException(
                f"Could not find any registered measurement with service class: '{service_class}'."
            )
        else:
            raise
    channel = channel_pool.get_channel(service_location.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def get_configuration_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse, service_class: str
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
        configuration_metadata[k] = configuration_metadata[k]._replace(default_value=v)

    return configuration_metadata


def get_output_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
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
            )
        )
    output_metadata = frame_metadata_dict(output_parameter_list)
    return output_metadata


def get_configuration_parameters_with_type_and_default_values(
    configuration_metadata: Dict[int, ParameterMetadata],
    built_in_import_modules: List[str],
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
            if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
                default_value = f"r{default_value}"
                parameter_type = "Path"
                built_in_import_modules.append(PATH_IMPORT)

        configuration_parameters.append(f"{parameter_name}: {parameter_type} = {default_value}")

    # Use newline and spaces to align the method parameters appropriately in the generated file.
    configuration_parameters_with_type_and_value = f",{os.linesep}        ".join(
        configuration_parameters
    )
    parameter_names_as_str = ", ".join(parameter_names)

    return (configuration_parameters_with_type_and_value, parameter_names_as_str)


def get_output_parameters_with_type(
    output_metadata: Dict[int, ParameterMetadata],
    built_in_import_modules: List[str],
    custom_import_modules: List[str],
) -> str:
    """Returns the output parameters of the measurement with type."""
    output_parameters_with_type = []
    for metadata in output_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_type = _get_python_type_as_str(metadata.type, metadata.repeated)

        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
            parameter_type = "Path"
            built_in_import_modules.append(PATH_IMPORT)

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            parameter_type = "DoubleXYData"
            custom_import_modules.append(XY_DATA_IMPORT)

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"

        output_parameters_with_type.append(f"{parameter_name}: {parameter_type}")

    return f"{os.linesep}    ".join(output_parameters_with_type)


def to_ordered_set(values: Iterable[_T]) -> AbstractSet[_T]:
    """Converts an iterable to an ordered set."""
    return dict.fromkeys(values).keys()


def camel_to_snake_case(camel_case_string: str) -> str:
    """Converts a camelCase string to a snake_case string."""
    partial = camel_case_string
    for regex in CAMEL_TO_SNAKE_CASE_REGEXES:
        partial = regex.sub(r"\1_\2", partial)

    return partial.lower()


def _remove_invalid_characters(input_string: str, new_char: str) -> str:
    # Replace any spaces or special characters with an '_'.
    if not input_string.isidentifier():
        for invalid_char in INVALID_CHARS:
            input_string = input_string.replace(invalid_char, new_char)

    if input_string[0].isdigit() or keyword.iskeyword(input_string):
        input_string = "_" + input_string

    return input_string


def _get_python_identifier(input_string: str) -> str:
    valid_identifier = input_string.lower()
    valid_identifier = _remove_invalid_characters(valid_identifier, "_")
    return valid_identifier


def _get_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    python_type = PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)

    if python_type is None:
        raise TypeError(f"Invalid data type: '{type}'.")

    if is_array:
        return f"List[{python_type.__name__}]"
    return python_type.__name__

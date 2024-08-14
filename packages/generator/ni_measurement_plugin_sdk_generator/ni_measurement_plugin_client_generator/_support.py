"""Support functions for the Measurement Plug-In Client generator."""

import keyword
from typing import Any, Callable, Dict, List, Tuple

import click
import grpc
from google.protobuf import descriptor_pool
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.parameter import decoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    create_file_descriptor,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient

from ni_measurement_plugin_sdk_generator.ni_measurement_plugin_client_generator._constants import (
    _IMPORT_MODULES,
    _INVALID_CHARS,
    _PATH_IMPORT,
    _PROTO_DATATYPE_TO_PYTYPE_LOOKUP,
    _V2_MEASUREMENT_SERVICE_INTERFACE,
    _XY_DATA_IMPORT,
    _CUSTOM_IMPORT_TYPE,
    _DEFAULT_IMPORT_TYPE,
)


def _is_measurement_service_running(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> str:
    try:
        if service_class:
            DiscoveryClient().resolve_service(_V2_MEASUREMENT_SERVICE_INTERFACE, service_class)
        return service_class
    except Exception:
        raise click.BadParameter(
            f"Could not find any registered measurement with service class: '{service_class}'."
        )


def _get_measurement_service_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)

    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _get_configuration_parameter_list(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    configuration_parameter_list = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        configuration_parameter_list.append(
            ParameterMetadata.initialize(
                validate_type=True,
                display_name=configuration.name,
                type=configuration.type,
                repeated=configuration.repeated,
                default_value=None,
                annotations=dict(configuration.annotations.items()),
                message_type=configuration.message_type,
            )
        )
    return configuration_parameter_list


def _get_output_parameter_list(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    output_parameter_list = []
    for output in metadata.measurement_signature.outputs:
        output_parameter_list.append(
            ParameterMetadata.initialize(
                validate_type=True,
                display_name=output.name,
                type=output.type,
                repeated=output.repeated,
                default_value=None,
                annotations=dict(output.annotations.items()),
                message_type=output.message_type,
            )
        )
    return output_parameter_list


def _frame_metadata_dict(
    parameter_list: List[ParameterMetadata],
) -> Dict[int, ParameterMetadata]:
    metadata_dict = {}
    for i, parameter in enumerate(parameter_list, start=1):
        metadata_dict[i] = parameter

    return metadata_dict


def _get_configuration_metadata(
    metadata: v2_measurement_service_pb2.GetMetadataResponse, service_class: str
) -> Dict[int, ParameterMetadata]:
    configuration_parameter_list = _get_configuration_parameter_list(metadata)
    output_parameter_list = _get_output_parameter_list(metadata)
    configuration_metadata = _frame_metadata_dict(configuration_parameter_list)

    create_file_descriptor(
        service_name=service_class,
        output_metadata=output_parameter_list,
        input_metadata=configuration_parameter_list,
        pool=descriptor_pool.Default(),
    )

    deserialized_paramers = decoder.deserialize_parameters(
        configuration_metadata,
        metadata.measurement_signature.configuration_defaults.value,
        service_class + ".Configurations",
    )

    default_values = [None] * deserialized_paramers.__len__()
    for k, v in deserialized_paramers.items():
        configuration_metadata[k] = configuration_metadata[k]._replace(default_value=v)
        default_values[k - 1] = v

    return configuration_metadata


def _get_output_metadata(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    output_parameter_list = _get_output_parameter_list(metadata)
    output_metadata = _frame_metadata_dict(output_parameter_list)
    return output_metadata


def _remove_invalid_characters(input_string: str, new_char: str) -> str:
    # Replace any spaces or special characters with an '_'.
    if not input_string.isidentifier():
        for invalid_char in _INVALID_CHARS:
            input_string = input_string.replace(invalid_char, new_char)

    if input_string[0].isdigit() or keyword.iskeyword(input_string):
        input_string = "_" + input_string

    return input_string


def _get_python_module_name(input_string: str) -> str:
    module_name = input_string.replace(" ", "_").lower()
    module_name = _remove_invalid_characters(module_name, "")
    return module_name


def _get_python_identifier(input_string: str) -> str:
    valid_identifier = input_string.lower()
    valid_identifier = _remove_invalid_characters(valid_identifier, "_")
    return valid_identifier


def _get_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    python_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)

    if python_type is None:
        raise Exception(
            "Invalid data type : The configurated data type is not of the expected type"
        )

    if is_array:
        return f"List[{python_type.__name__}]"
    return python_type.__name__


def _get_configuration_parameters_with_type_and_values(
    configuration_metadata: Dict[int, ParameterMetadata]
) -> Tuple[str, str]:
    configuration_parameters = []
    parameter_names = []

    for metadata in configuration_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_names.append(parameter_name)

        default_value = metadata.default_value
        parameter_type = _handle_exception(
            lambda: _get_python_type_as_str(metadata.type, metadata.repeated)
        )
        if isinstance(default_value, str):
            default_value = f'"{default_value}"'

            # If it's path type, make the value as raw string literal to ignore escape characters.
            if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
                default_value = f"r{default_value}"
                parameter_type = "Path"
                _IMPORT_MODULES[parameter_type] = _PATH_IMPORT

        configuration_parameters.append(f"{parameter_name}: {parameter_type} = {default_value}")

    # Use newline and spaces to align the method parameters appropriately in the generated file.
    configuration_parameters_with_type_and_value = ",\n        ".join(configuration_parameters)
    parameter_names_as_str = ", ".join(parameter_names)

    return (configuration_parameters_with_type_and_value, parameter_names_as_str)


def _get_output_parameters_with_type(
    output_metadata: Dict[int, ParameterMetadata],
) -> str:
    output_parameters_with_type = []
    for metadata in output_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_type = _handle_exception(
            lambda: _get_python_type_as_str(metadata.type, metadata.repeated)
        )

        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
            parameter_type = "Path"
            _IMPORT_MODULES[_PATH_IMPORT] = _DEFAULT_IMPORT_TYPE

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            parameter_type = "DoubleXYData"
            _IMPORT_MODULES[_XY_DATA_IMPORT] = _CUSTOM_IMPORT_TYPE

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"

        output_parameters_with_type.append(f"{parameter_name}: {parameter_type}")

    return "\n    ".join(output_parameters_with_type)


def _handle_exception(method: Callable[[], Any]) -> Any:
    try:
        return method()
    except Exception as ex:
        print(ex)

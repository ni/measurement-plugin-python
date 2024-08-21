"""Support functions for the Measurement Plug-In Client generator."""

import keyword
from enum import Enum
from typing import Dict, Tuple

from google.protobuf import descriptor_pool
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.grpc_servicer import frame_metadata_dict
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.parameter import (
    decoder,
    serialization_descriptors,
)

from ni_measurement_plugin_sdk_generator.client._constants import (
    INVALID_CHARS,
    PATH_IMPORT,
    PROTO_DATATYPE_TO_PYTYPE_LOOKUP,
    V2_MEASUREMENT_SERVICE_INTERFACE,
    XY_DATA_IMPORT,
)


class ImportType(Enum):
    """Type for import  modules."""

    BUILT_IN = 1
    CUSTOM = 2


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
    except Exception:
        raise RuntimeError(
            f"Could not find any registered measurement with service class: '{service_class}'."
        )
    channel = channel_pool.get_channel(service_location.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def get_configuration_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse, service_class: str
) -> Dict[int, ParameterMetadata]:
    """Returns the configuration metadata of the measurement."""
    configuration_parameter_list =  []
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

    serialization_descriptors.create_file_descriptor(
        input_metadata=configuration_parameter_list,
        output_metadata=output_parameter_list,
        service_name=service_class,
        pool=descriptor_pool.Default(),
    )
    configuration_metadata = frame_metadata_dict(configuration_parameter_list)
    deserialized_parameters = decoder.deserialize_parameters(
        configuration_metadata,
        metadata.measurement_signature.configuration_defaults.value,
        service_class + ".Configurations",
    )

    default_values = [None] * len(deserialized_parameters)
    for k, v in deserialized_parameters.items():
        configuration_metadata[k] = configuration_metadata[k]._replace(default_value=v)
        default_values[k - 1] = v

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


def _remove_invalid_characters(input_string: str, new_char: str) -> str:
    # Replace any spaces or special characters with an '_'.
    if not input_string.isidentifier():
        for invalid_char in INVALID_CHARS:
            input_string = input_string.replace(invalid_char, new_char)

    if input_string[0].isdigit() or keyword.iskeyword(input_string):
        input_string = "_" + input_string

    return input_string


def get_python_module_name(input_string: str) -> str:
    """Returns a valid name python module."""
    module_name = input_string.replace(" ", "_").lower()
    module_name = _remove_invalid_characters(module_name, "")
    return module_name


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


def get_configuration_parameters_with_type_and_default_values(
    configuration_metadata: Dict[int, ParameterMetadata],
    import_modules: Dict[str, str],
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
                import_modules[PATH_IMPORT] = ImportType.BUILT_IN.name

        configuration_parameters.append(f"{parameter_name}: {parameter_type} = {default_value}")

    # Use newline and spaces to align the method parameters appropriately in the generated file.
    configuration_parameters_with_type_and_value = ",\n        ".join(configuration_parameters)
    parameter_names_as_str = ", ".join(parameter_names)

    return (configuration_parameters_with_type_and_value, parameter_names_as_str)


def get_output_parameters_with_type(
    output_metadata: Dict[int, ParameterMetadata],
    import_modules: Dict[str, str],
) -> str:
    """Returns the output parameters of the measurement with type."""
    output_parameters_with_type = []
    for metadata in output_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_type = _get_python_type_as_str(metadata.type, metadata.repeated)

        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
            parameter_type = "Path"
            import_modules[PATH_IMPORT] = ImportType.BUILT_IN.name

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            parameter_type = "DoubleXYData"
            import_modules[XY_DATA_IMPORT] = ImportType.CUSTOM.name

            if metadata.repeated:
                parameter_type = f"List[{parameter_type}]"

        output_parameters_with_type.append(f"{parameter_name}: {parameter_type}")

    return "\n    ".join(output_parameters_with_type)

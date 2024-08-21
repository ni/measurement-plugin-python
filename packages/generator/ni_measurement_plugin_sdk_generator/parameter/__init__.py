"""Support functions for the Measurement Plug-In Client."""

from typing import Any, Dict, List, Sequence

from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.parameter import decoder, encoder
from ni_measurement_plugin_sdk_service._internal.parameter import serialization_descriptors
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)


def get_configuration_parameters(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    """Return the list of configuration parameters of the measurement."""
    configuration_parameters = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        configuration_parameters.append(
            ParameterMetadata.initialize(
                display_name=configuration.name,
                type=configuration.type,
                repeated=configuration.repeated,
                default_value=None,
                annotations=dict(configuration.annotations.items()),
                message_type=configuration.message_type,
            )
        )
    return configuration_parameters


def get_output_parameters(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    """Return the list of output parameters of the measurement."""
    output_parameters = []
    for output in metadata.measurement_signature.outputs:
        output_parameters.append(
            ParameterMetadata.initialize(
                display_name=output.name,
                type=output.type,
                repeated=output.repeated,
                default_value=None,
                annotations=dict(output.annotations.items()),
                message_type=output.message_type,
            )
        )
    return output_parameters


def create_file_descriptor(
    metadata: v2_measurement_service_pb2.GetMetadataResponse, service_name: str
) -> None:
    """Creates two message types in one file descriptor proto.

    Args:
        metadata (measurement_service_pb2.GetMetadataResponse): Measurement metadata.

        service_name (str): Unique service name.
    """
    configuration_parameter_list = get_configuration_parameters(metadata)
    output_parameter_list = get_output_parameters(metadata)

    serialization_descriptors.create_file_descriptor(
        service_name=service_name,
        output_metadata=output_parameter_list,
        input_metadata=configuration_parameter_list,
        pool=descriptor_pool.Default(),
    )


def deserialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_bytes: bytes,
    service_name: str,
) -> Dict[int, Any]:
    """Deserialize the bytes of the parameter based on the metadata.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_bytes (bytes): Byte string to deserialize.

        service_name (str): Unique service name.

    Returns:
        Dict[int, Any]: Deserialized parameters by ID.
    """
    return decoder.deserialize_parameters(
        parameter_metadata_dict=parameter_metadata_dict,
        parameter_bytes=parameter_bytes,
        service_name=service_name,
    )


def serialize_parameters(
    parameter_metadata_dict: Dict[int, ParameterMetadata],
    parameter_values: Sequence[Any],
    service_name: str,
) -> bytes:
    """Serialize the parameter values in same order based on the metadata_dict.

    Args:
        parameter_metadata_dict (Dict[int, ParameterMetadata]): Parameter metadata by ID.

        parameter_values (Sequence[Any]): Parameter values to serialize.

        service_name (str): Unique service name.

    Returns:
        bytes: Serialized byte string containing parameter values.
    """
    return encoder.serialize_parameters(
        parameter_metadata_dict=parameter_metadata_dict,
        parameter_values=parameter_values,
        service_name=service_name,
    )

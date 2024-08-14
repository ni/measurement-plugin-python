"""Support functions for the Measurement Plug-In Client."""

from typing import Any, Dict, List

import grpc
from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.parameter import encoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    create_file_descriptor,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient, ServiceLocation

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


def _get_resolved_service(discovery_client: DiscoveryClient, service_class: str) -> ServiceLocation:
    try:
        resolved_service = discovery_client.resolve_service(
            provided_interface=_V2_MEASUREMENT_SERVICE_INTERFACE, 
            service_class=service_class
        )
        return resolved_service
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise RuntimeError(
                "Failed to connect to the measurement service. Ensure if the measurement is running."
            )
        raise


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
                annotations=configuration.annotations,
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
                annotations=output.annotations,
                message_type=output.message_type,
            )
        )
    return output_parameter_list


def _create_file_descriptor(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    service_class : str
) -> None:
    configuration_parameter_list = _get_configuration_parameter_list(metadata)
    output_parameter_list = _get_output_parameter_list(metadata)

    create_file_descriptor(
        service_name=service_class,
        output_metadata=output_parameter_list,
        input_metadata=configuration_parameter_list,
        pool=descriptor_pool.Default(),
    )    


def _get_measure_request(
    service_class : str,
    configuration_metadata : Dict[int, ParameterMetadata],
    args: Any
) -> v2_measurement_service_pb2.MeasureRequest:
    serialized_configuration = any_pb2.Any(
        value=encoder.serialize_parameters(
            parameter_metadata_dict=configuration_metadata, 
            parameter_values=args, 
            service_name=service_class +  ".Configurations"
        )
    )
    return v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=serialized_configuration
    )

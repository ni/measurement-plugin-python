<%page args="configuration_metadata, output_metadata, service_class, method_signature, params, return_types"/>\
\
"""Python measurement client."""

from typing import Any, List, Tuple

import grpc
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.parameter.serializer import (
    deserialize_parameters,
    serialize_parameters,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.pin_map import PinMapClient

V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
SITES = [0]

configuration_metadata_by_id = ${configuration_metadata}
output_metadata_by_id = ${output_metadata}
pin_map_path = ""

def _get_measurement_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        V2_MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _get_measure_request(config_data, args) -> v2_measurement_service_pb2.MeasureRequest:
    values = [arg for arg in args]
    serialized_configuration = any_pb2.Any(value=serialize_parameters(config_data, values))
    return v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=serialized_configuration,
        pin_map_context=PinMapContext(
            pin_map_id=pin_map_path,
            sites=SITES,
        ),
    )


def _measure(service_class: str, *args) -> Tuple[Any]:
    discovery_client = DiscoveryClient()
    stub = _get_measurement_stub(discovery_client, service_class)
    request = _get_measure_request(configuration_metadata_by_id, args)
    result: Tuple = ()
    for response in stub.Measure(request):
        output_values = deserialize_parameters(output_metadata_by_id, response.outputs.value)
        for k, v in output_values.items():
            result = result + (v,)

    return result


def measure(
    ${method_signature}
) -> Tuple[${return_types}]:
    """Runs the measurement with the parameter values.

    Returns:
        Measurement output.
    """
    return _measure(
        "${service_class}",
        ${params}
    )


def register_pin_map(pin_map_absolute_path: str) -> str:
    """Registers the pin map with the pin map service.

    Args:
        pin_map_absolute_path: Absolute path of the pin map.

    Returns:
        str: Pin map id.
    """
    pin_map_client = PinMapClient()
    global pin_map_path 
    pin_map_path = pin_map_absolute_path
    
    return pin_map_client.update_pin_map(pin_map_path)

<%page args="measure_docstring, configuration_metadata, output_metadata, service_class, measure_parameters_with_type, measure_parameters, enum_by_class_name, measure_return_values_with_type"/>\
\
"""Python measurement client."""

% if enum_by_class_name:
from enum import Enum
% endif
from typing import Any, Dict, List, NamedTuple, Tuple

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

_SITES = [0]
_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

configuration_metadata_by_id = ${configuration_metadata}
output_metadata_by_id = ${output_metadata}
pin_map_path = ""


def _get_measurement_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _get_measure_request(
    configuration_metadata: Dict[int, ParameterMetadata], args: Any
) -> v2_measurement_service_pb2.MeasureRequest:
    serialized_configuration = any_pb2.Any(
        value=serialize_parameters(configuration_metadata, list(args))
    )
    return v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=serialized_configuration,
        pin_map_context=PinMapContext(
            pin_map_id=pin_map_path,
            sites=_SITES,
        ),
    )

% if enum_by_class_name:

def _get_enum_type(parameter_metadata: ParameterMetadata) -> type:
    if parameter_metadata.repeated and len(parameter_metadata.default_value) > 0:
        if isinstance(parameter_metadata.default_value[0], str):
            return type(eval(parameter_metadata.default_value[0]))
        return type(parameter_metadata.default_value[0])
    elif isinstance(parameter_metadata.default_value, str):
        return type(eval(parameter_metadata.default_value))
    else:
        return type(parameter_metadata.default_value)


def _parse_enum_values(output_metadata_by_id: Dict[int, ParameterMetadata], output_values: Dict[int, Any]) -> Dict[int, Any]:
    for key, metadata in output_metadata_by_id.items():
        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_type = _get_enum_type(metadata)
            output_values[key] = enum_type(int(output_values[key]))

    return output_values

% endif

def _measure(service_class: str, *args: Any) -> Tuple[Any]:
    discovery_client = DiscoveryClient()
    stub = _get_measurement_stub(discovery_client, service_class)
    request = _get_measure_request(configuration_metadata_by_id, args)
    result = [None] * max(output_metadata_by_id.keys())
    for response in stub.Measure(request):
        output_values = deserialize_parameters(output_metadata_by_id, response.outputs.value)
        % if enum_by_class_name:
        output_values = _parse_enum_values(output_metadata_by_id, output_values)
        % endif
        for k, v in output_values.items():
            result[k - 1] = v

    return tuple(result)

% for enum_name, enum_value in enum_by_class_name.items():
<% class_line = f"class {enum_name}(Enum):" %>
${class_line}\
    % for key, val in enum_value.items():
    <% content_line = f"{key} = {val}" %>
    ${content_line}\
    % endfor


% endfor

class Output(NamedTuple):
    """Measurement result container."""

    ${measure_return_values_with_type}


def measure(
    ${measure_parameters_with_type}
) -> Output:
    """${measure_docstring}

    Returns:
        Measurement output.
    """
    response = _measure(
        "${service_class}",
        ${measure_parameters}
    )
    return Output._make(response)


def register_pin_map(pin_map_absolute_path: str) -> str:
    """Registers the pin map with the pin map service.

    Args:
        pin_map_absolute_path: Absolute path of the pin map.

    Returns:
        Pin map id.
    """
    pin_map_client = PinMapClient()
    global pin_map_path
    pin_map_path = pin_map_absolute_path

    return pin_map_client.update_pin_map(pin_map_path)

<%page args="measure_docstring, configuration_metadata, output_metadata, service_class, measure_parameters_with_type, measure_parameters, measure_return_values_with_type, enum_by_class_name,import_modules"/>\
\
"""Python measurement client."""

from functools import cached_property
from typing import List

import grpc
from ni_measurement_plugin_sdk_service._internal.parameter import decoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
% for module in import_modules.values():
${module}
% endfor
from _helpers import (
    _create_file_descriptor,
    _get_measure_request,
    _parse_enum_values,
    <% output_type = "None" %>\
    % if output_metadata:
    Output,
    <% output_type = "Output" %>\
    % endif
    % for enum_name in enum_by_class_name.keys():
    ${enum_name},
    % endfor
)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

class MeasurementClient:
     
    def __init__(self):
        self._service_class = "${service_class}"
        self._discovery_client = DiscoveryClient()
        self._metadata = self._measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        self._configuration_metadata = ${configuration_metadata}
        self._output_metadata = ${output_metadata}
        _create_file_descriptor(self._metadata, self._service_class)
        
    @cached_property
    def _measurement_service_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        try:
            resolved_service = self._discovery_client.resolve_service(
                _V2_MEASUREMENT_SERVICE_INTERFACE, self._service_class
            )
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise RuntimeError(
                    "Failed to connect to the measurement service. Ensure if the measurement is running."
                )
            raise

        channel = grpc.insecure_channel(resolved_service.insecure_address)
        return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
    
    def Measure(
        self,
        ${measure_parameters_with_type}
    ) -> ${output_type} :
        """${measure_docstring}

        Returns:
            Measurement output.
        """

        request = _get_measure_request(
            self._service_class, 
            self._configuration_metadata, 
            [${measure_parameters}]
        )
        % if output_metadata:
        result = [None] * max(self._output_metadata.keys())
        % else:
        result = []
        % endif

        for response in self._measurement_service_stub.Measure(request):
            output_values = decoder.deserialize_parameters(
                self._output_metadata, response.outputs.value, self._service_class + ".Outputs"
            )
            % if output_metadata:
            output_values = _parse_enum_values(self._output_metadata, output_values)
            % endif

            for k, v in output_values.items():
                result[k - 1] = v

        return Output._make(result)

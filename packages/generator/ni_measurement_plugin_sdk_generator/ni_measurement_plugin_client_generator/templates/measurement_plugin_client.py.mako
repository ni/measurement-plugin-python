<%page args="measure_docstring, configuration_metadata, output_metadata, service_class, configuration_parameters_with_type_and_values, measure_api_parameters, output_parameters_with_type, import_modules"/>\
\
"""Python Measurement Plug-In Client."""

from functools import cached_property
% for module, type in import_modules.items():
% if type == "In-Built":
${module}
% endif
% endfor
from typing import List, NamedTuple

import grpc
from _helpers import (
    _create_file_descriptor,
    _get_measure_request,
    _get_resolved_service,
)
from ni_measurement_plugin_sdk_service._internal.parameter import decoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
% for module, type in import_modules.items():
% if type == "Custom":
${module}
% endif
% endfor
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient

<% output_type = "None" %>\
% if output_metadata:

class Output(NamedTuple):
    """Measurement result container."""

    ${output_parameters_with_type}
<% output_type = "Output" %>\
% endif


class MeasurementPlugInClient:
    """Client for accessing the Measurement Plug-In measurement services."""
     
    def __init__(self):
        """Initialize the Measurement Plug-In client."""
        self._service_class = "${service_class}"
        self._discovery_client = DiscoveryClient()
        self._metadata = self._measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        self._configuration_metadata = ${configuration_metadata}
        self._output_metadata = ${output_metadata}
        _create_file_descriptor(self._metadata, self._service_class)
        
    @cached_property
    def _measurement_service_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        resolved_service = _get_resolved_service(self._discovery_client, self._service_class)
        channel = grpc.insecure_channel(resolved_service.insecure_address)
        return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
    
    def measure(
        self,
        ${configuration_parameters_with_type_and_values}
    ) -> ${output_type} :
        """${measure_docstring}

        Returns:
            Measurement output.
        """
        request = _get_measure_request(
            self._service_class, 
            self._configuration_metadata, 
            [${measure_api_parameters}]
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

            for k, v in output_values.items():
                result[k - 1] = v

        return Output._make(result)

<%page args="class_name, measure_docstring, configuration_metadata, output_metadata, service_class, configuration_parameters_with_type_and_default_values, measure_api_parameters, output_parameters_with_type, import_modules"/>\
\
"""Python Measurement Plug-In Client."""

import threading
% for module, import_type in import_modules.items():
% if import_type == "BUILT_IN":
${module}
% endif
% endfor
from typing import List, NamedTuple

import grpc
from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
% for module, import_type in import_modules.items():
% if import_type == "CUSTOM":
${module}
% endif
% endfor
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.parameter import (
    decoder,
    encoder,
    serialization_descriptors,
    ParameterMetadata,
)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

<% output_type = "None" %>\
% if output_metadata:

class Output(NamedTuple):
    """Measurement result container."""

    ${output_parameters_with_type}
<% output_type = "Output" %>\
% endif


class ${class_name}:
    """Client for accessing the Measurement Plug-In measurement services."""
     
    def __init__(self):
        """Initialize the Measurement Plug-In client."""
        self._initialization_lock = threading.Lock()
        self._service_class = "${service_class}"
        self._channel_pool = GrpcChannelPool()
        self._discovery_client = DiscoveryClient(grpc_channel_pool=self._channel_pool)
        self._metadata = self._measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        self._configuration_metadata = ${configuration_metadata}
        self._output_metadata = ${output_metadata}
        
    @property
    def _measurement_service_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        with self._initialization_lock:
            try:
                service_location = self._discovery_client.resolve_service(
                    _V2_MEASUREMENT_SERVICE_INTERFACE, self._service_class
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    raise RuntimeError(
                        "Failed to connect to the measurement service. Ensure if the measurement is running."
                    )
                raise
            channel = self._channel_pool.get_channel(service_location.insecure_address)
            return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
    
    def _create_file_descriptor(self) -> None:
        input_metadata =  []        
        for configuration in self.metadata.measurement_signature.configuration_parameters:
            input_metadata.append(
                ParameterMetadata.initialize(
                    display_name=configuration.name,
                    type=configuration.type,
                    repeated=configuration.repeated,
                    default_value=None,
                    annotations=dict(configuration.annotations.items()),
                    message_type=configuration.message_type,
                )
            )

        output_metadata = []
        for output in self.metadata.measurement_signature.outputs:
            output_metadata.append(
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
            input_metadata=input_metadata,
            output_metadata=output_metadata,
            service_name=self._service_class,
            pool=descriptor_pool.Default(),
        )

    def measure(
        self,
        ${configuration_parameters_with_type_and_default_values}
    ) -> ${output_type} :
        """${measure_docstring}

        Returns:
            Measurement output.
        """
        parameter_values = [${measure_api_parameters}]
        serialized_configuration = any_pb2.Any(
            value=encoder.serialize_parameters(
                parameter_metadata_dict=self._configuration_metadata, 
                parameter_values=parameter_values, 
                service_name=self._service_class +  ".Configurations"
            )
        )
        request = v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration
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

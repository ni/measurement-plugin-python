<%page args="class_name, display_name, configuration_metadata, output_metadata, service_class, configuration_parameters_with_type_and_default_values, measure_api_parameters, output_parameters_with_type, built_in_import_modules, custom_import_modules"/>\
\
"""Python Measurement Plug-In Client."""

import logging
import threading
from functools import cached_property
% for module in built_in_import_modules:
${module}
% endfor
from typing import Any, Generator, List, NamedTuple, Optional

import grpc
from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
% for module in custom_import_modules:
${module}
% endfor
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    create_file_descriptor,
    deserialize_parameters,
    ParameterMetadata,
    serialize_parameters,
)
from ni_measurement_plugin_sdk_service.pin_map import PinMapClient

_logger = logging.getLogger(__name__)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

<% output_type = "None" %>\
% if output_metadata:

class Output(NamedTuple):
    """Measurement result container."""

    ${output_parameters_with_type}
<% output_type = "Output" %>\
% endif


class ${class_name}:
    """Client to interact with the measurement plug-in."""
     
    def __init__(
        self,
        *,
        discovery_client: Optional[DiscoveryClient] = None,
        grpc_channel: Optional[grpc.Channel] = None,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ):
        """Initialize the Measurement Plug-In Client.

        Args:
            discovery_client: An optional discovery client.

            grpc_channel: An optional gRPC channel targeting a measurement service.

            grpc_channel_pool: An optional gRPC channel pool.
        """
        self._initialization_lock = threading.Lock()
        self._service_class = "${service_class}"
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._stub: Optional[v2_measurement_service_pb2_grpc.MeasurementServiceStub] = None
        self._configuration_metadata = ${configuration_metadata}
        self._output_metadata = ${output_metadata}
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()
        self.pin_map_id: str = ""
        self.sites: list[int] = [0]

    @cached_property
    def pin_map_client(self) -> PinMapClient:
        return PinMapClient(
            discovery_client=self._discovery_client, grpc_channel_pool=self._grpc_channel_pool
        )

    def _get_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    _logger.debug("Creating unshared GrpcChannelPool.")
                    self._grpc_channel_pool = GrpcChannelPool()
                if self._discovery_client is None:
                    _logger.debug("Creating unshared DiscoveryClient.")
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._grpc_channel_pool
                    )
                if self._stub is None:
                    service_location = self._discovery_client.resolve_service(
                        provided_interface=_V2_MEASUREMENT_SERVICE_INTERFACE,
                        service_class=self._service_class,
                    )
                    channel = self._grpc_channel_pool.get_channel(service_location.insecure_address)
                    self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        return self._stub

    def _create_file_descriptor(self) -> None:
        metadata = self._get_stub().GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        configuration_metadata =  []        
        for configuration in metadata.measurement_signature.configuration_parameters:
            configuration_metadata.append(
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
        for output in metadata.measurement_signature.outputs:
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

        create_file_descriptor(
            input_metadata=configuration_metadata,
            output_metadata=output_metadata,
            service_name=self._service_class,
            pool=descriptor_pool.Default(),
        )

    def _create_measure_request(
        self, parameter_values: List[Any]
    ) -> v2_measurement_service_pb2.MeasureRequest:
        serialized_configuration = any_pb2.Any(
            value=serialize_parameters(
                parameter_metadata_dict=self._configuration_metadata,
                parameter_values=parameter_values,
                service_name=f"{self._service_class}.Configurations",
            )
        )
        return v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration,
            pin_map_context=PinMapContext(pin_map_id=self.pin_map_id, sites=self.sites),
        )

    def _deserialize_response(
        self, response: v2_measurement_service_pb2.MeasureResponse
    ) -> Output:
        if self._output_metadata:
            result = [None] * max(self._output_metadata.keys())
        else:
            result = []
        output_values = deserialize_parameters(
            self._output_metadata, response.outputs.value, f"{self._service_class}.Outputs"
        )

        for k, v in output_values.items():
            result[k - 1] = v
        return Output._make(result)

    def measure(
        self,
        ${configuration_parameters_with_type_and_default_values}
    ) -> ${output_type} :
        """Executes the ${display_name}.

        Returns:
            Measurement output.
        """
        parameter_values = [${measure_api_parameters}]
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            result = self._deserialize_response(response)
        return result

    def stream_measure(
        self,
        ${configuration_parameters_with_type_and_default_values}
    ) -> Generator[${output_type}, None, None] :
        """Executes the ${display_name}.

        Returns:
            Stream of measurement output.
        """
        parameter_values = [${measure_api_parameters}]
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            yield self._deserialize_response(response)

    def register_pin_map(self, pin_map_path: str) -> str:
        """Registers the pin map with the pin map service.
        
        Args:
            pin_map_path: Absolute path of the pin map file.

        Returns:
            Registered pin map id.
        """
        self.pin_map_id = self.pin_map_client.update_pin_map(pin_map_path)

        return self.pin_map_id

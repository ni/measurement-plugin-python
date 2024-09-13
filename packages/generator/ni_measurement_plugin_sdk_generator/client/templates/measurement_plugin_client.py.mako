<%page args="class_name, display_name, configuration_metadata, output_metadata, service_class, configuration_parameters_with_type_and_default_values, measure_api_parameters, output_parameters_with_type, built_in_import_modules, custom_import_modules"/>\
\
"""Generated client API for the ${display_name | repr} measurement plug-in."""

import logging
import threading
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

_logger = logging.getLogger(__name__)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

<% output_type = "None" %>\
% if output_metadata:

class Outputs(NamedTuple):
    """Outputs for the ${display_name | repr} measurement plug-in."""

    ${output_parameters_with_type}
<% output_type = "Outputs" %>\
% endif


class ${class_name}:
    """Client for the ${display_name | repr} measurement plug-in."""
     
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
        self._initialization_lock = threading.RLock()
        self._service_class = ${service_class | repr}
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._stub: Optional[v2_measurement_service_pb2_grpc.MeasurementServiceStub] = None
        self._measure_response: Optional[
            Generator[v2_measurement_service_pb2.MeasureResponse, None, None]
        ] = None
        self._configuration_metadata = ${configuration_metadata}
        self._output_metadata = ${output_metadata}
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()
        
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
            configuration_parameters=serialized_configuration
        )

    % if output_metadata:
    def _deserialize_response(
        self, response: v2_measurement_service_pb2.MeasureResponse
    ) -> Outputs:
        if self._output_metadata:
            result = [None] * max(self._output_metadata.keys())
        else:
            result = []
        output_values = deserialize_parameters(
            self._output_metadata, response.outputs.value, f"{self._service_class}.Outputs"
        )

        for k, v in output_values.items():
            result[k - 1] = v
        return Outputs._make(result)
    
    % endif
    % if "from pathlib import Path" in built_in_import_modules:
    def _convert_paths_to_strings(self, parameter_values: List[Any]) -> List[Any]:
        result: List[Any] = []

        for parameter_value in parameter_values:
            if isinstance(parameter_value, list):
                converted_list = []
                for value in parameter_value:
                    if isinstance(value, Path):
                        converted_list.append(str(value))
                    else:
                        converted_list.append(value)
                result.append(converted_list)
            elif isinstance(parameter_value, Path):
                result.append(str(parameter_value))
            else:
                result.append(parameter_value)
        return result
    % endif

    def measure(
        self,
        ${configuration_parameters_with_type_and_default_values}
    ) -> ${output_type} :
        """Perform a single measurement.

        Returns:
            Measurement outputs.
        """
        stream_measure_response = self.stream_measure(
            ${measure_api_parameters}
        )
        for response in stream_measure_response:
        % if output_metadata:
            result = response
        return result
        % else:
            pass
        % endif

    def stream_measure(
        self,
        ${configuration_parameters_with_type_and_default_values}
    ) -> Generator[${output_type}, None, None] :
        """Perform a streaming measurement.

        Returns:
            Stream of measurement outputs.
        """
        % if "from pathlib import Path" in built_in_import_modules:
        parameter_values = self._convert_paths_to_strings([${measure_api_parameters}])
        % else:
        parameter_values = [${measure_api_parameters}]
        % endif
        with self._initialization_lock:
            if self._measure_response is not None:
                raise RuntimeError(
                    "A measurement is currently in progress. To make concurrent measurement requests, please create a new client instance."
                )
            request = self._create_measure_request(parameter_values)
            self._measure_response = self._get_stub().Measure(request)

        try:
            for response in self._measure_response:
                % if output_metadata:
                yield self._deserialize_response(response)
                % else:
                yield
                % endif
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                _logger.debug("The measurement is canceled.")
            raise
        finally:
            with self._initialization_lock:
                self._measure_response = None

    def cancel(self) -> bool:
        """Cancels the active measurement call."""
        with self._initialization_lock:
            if self._measure_response:
                return self._measure_response.cancel()
            else:
                return False

<%!
import re
from typing import Any
%>\
\
<%page args="class_name, display_name, version, configuration_metadata, output_metadata, service_class, configuration_parameters_with_type_and_default_values, measure_api_parameters, output_parameters_with_type, built_in_import_modules, custom_import_modules, enum_by_class_name, configuration_parameters_type_url, outputs_message_type"/>\
\
<%
    def _format_default_value(value: Any) -> Any:
        if isinstance(value, str):
            return repr(value)
        else:
            return value
%>\
\

"""Generated client API for the ${display_name | repr} measurement plug-in."""

from __future__ import annotations

import logging
import pathlib
import threading
import typing
% if output_metadata:
import warnings
% endif
% if len(enum_by_class_name):
from enum import Enum
% endif

import grpc
from google.protobuf import any_pb2, descriptor_pool
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
% for module in custom_import_modules:
${module}
% endfor
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
% if output_metadata:
from ni_measurement_plugin_sdk_service.measurement import WrongMessageTypeWarning
% endif
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    ParameterMetadata,
    create_file_descriptor,
% if output_metadata:
    deserialize_parameters,
% endif
    serialize_parameters,
)
from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import PinMapContext

_logger = logging.getLogger(__name__)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

% for enum_name, enum_value in enum_by_class_name.items():

class ${enum_name.__name__}(Enum):
    """${enum_name.__name__} used for enum-typed measurement configs and outputs."""

    % for key, val in enum_value.items():
    ${key} = ${val}
    % endfor
% endfor

<% output_type = "None" %>\
% if output_metadata:

class Outputs(typing.NamedTuple):
    """Outputs for the ${display_name | repr} measurement plug-in."""

    % for output_parameter in output_parameters_with_type:
    ${output_parameter}
    % endfor
<% output_type = "Outputs" %>\
% endif


class ${class_name}:
    """Client for the ${display_name | repr} measurement plug-in."""
     
    def __init__(
        self,
        *,
        discovery_client: DiscoveryClient | None = None,
        pin_map_client: PinMapClient | None = None,
        grpc_channel: grpc.Channel | None = None,
        grpc_channel_pool: GrpcChannelPool | None = None,
    ):
        """Initialize the Measurement Plug-In Client.

        Args:
            discovery_client: An optional discovery client.

            pin_map_client: An optional pin map client.

            grpc_channel: An optional gRPC channel targeting a measurement service.

            grpc_channel_pool: An optional gRPC channel pool.
        """
        self._initialization_lock = threading.RLock()
        self._service_class = ${service_class | repr}
        self._version = ${version | repr}
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._pin_map_client = pin_map_client
        self._stub: v2_measurement_service_pb2_grpc.MeasurementServiceStub | None = None
        self._measure_response: None | (
            grpc._CallIterator[v2_measurement_service_pb2.MeasureResponse]
        ) = None
        self._configuration_metadata = {
            % for key, value in configuration_metadata.items():
            ${key}: ParameterMetadata(
                display_name=${value.display_name | repr},
                type=Field.Kind.ValueType(${value.type}),
                repeated=${value.repeated},
                default_value=${_format_default_value(value.default_value)},
                annotations=${value.annotations | n, repr},
                message_type=${value.message_type | repr},
                field_name=${value.field_name | repr},
                % if value.enum_type:
                enum_type=${value.enum_type.__name__}
                % else:
                enum_type=${value.enum_type}
                % endif
            ),  
            % endfor
        }
        self._output_metadata = {
            % for key, value in output_metadata.items():
            ${key}: ParameterMetadata(
                display_name=${value.display_name | repr},
                type=Field.Kind.ValueType(${value.type}),
                repeated=${value.repeated},
                default_value=${value.default_value},
                annotations=${value.annotations | n, repr},
                message_type=${value.message_type | repr},
                field_name=${value.field_name | repr},
                % if value.enum_type:
                enum_type=${value.enum_type.__name__}
                % else:
                enum_type=${value.enum_type}
                % endif
            ),  
            % endfor
        }
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()
        self._pin_map_context: PinMapContext = PinMapContext(pin_map_id="", sites=[0])

    @property
    def pin_map_context(self) -> PinMapContext:
        """The pin map context for the measurement."""
        return self._pin_map_context

    @pin_map_context.setter
    def pin_map_context(self, val: PinMapContext) -> None:
        if not isinstance(val, PinMapContext):
            raise TypeError(
                f"Invalid type {type(val)}: The given value must be an instance of PinMapContext."
            )
        self._pin_map_context = val

    @property
    def sites(self) -> list[int] | None:
        """The sites where the measurement must be executed."""
        return self._pin_map_context.sites

    @sites.setter
    def sites(self, val: list[int]) -> None:
        if self._pin_map_context is None:
            raise AttributeError(
                "Cannot set sites because the pin map context is None. Please provide a pin map context or register a pin map before setting sites."
            )
        self._pin_map_context = self._pin_map_context._replace(sites=val)

    def _get_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._stub is None:
                    service_location = self._get_discovery_client().resolve_service(
                        provided_interface=_V2_MEASUREMENT_SERVICE_INTERFACE,
                        service_class=self._service_class,
                        version=self._version,
                    )
                    channel = self._get_grpc_channel_pool().get_channel(service_location.insecure_address)
                    self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        return self._stub

    def _get_discovery_client(self) -> DiscoveryClient:
        if self._discovery_client is None:
            with self._initialization_lock:
                if self._discovery_client is None:
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._get_grpc_channel_pool(),
                    )
        return self._discovery_client

    def _get_grpc_channel_pool(self) -> GrpcChannelPool:
        if self._grpc_channel_pool is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    self._grpc_channel_pool = GrpcChannelPool()
        return self._grpc_channel_pool

    def _get_pin_map_client(self) -> PinMapClient:
        if self._pin_map_client is None:
            with self._initialization_lock:
                if self._pin_map_client is None:
                    self._pin_map_client = PinMapClient(
                        discovery_client=self._get_discovery_client(), 
                        grpc_channel_pool=self._get_grpc_channel_pool(),
                    )
        return self._pin_map_client

    def _create_file_descriptor(self) -> None:
        create_file_descriptor(
            input_metadata=list(self._configuration_metadata.values()),
            output_metadata=list(self._output_metadata.values()),
            service_name=self._service_class,
            pool=descriptor_pool.Default(),
        )

    def _create_measure_request(
        self, parameter_values: list[typing.Any]
    ) -> v2_measurement_service_pb2.MeasureRequest:
        serialized_configuration = any_pb2.Any(
            type_url=${configuration_parameters_type_url | repr},
            value=serialize_parameters(
                self._configuration_metadata,
                parameter_values,
                f"{self._service_class}.Configurations",
            )
        )
        return v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration,
            pin_map_context=self._pin_map_context._to_grpc(),
        )

    % if output_metadata:
    def _deserialize_response(
        self, response: v2_measurement_service_pb2.MeasureResponse
    ) -> Outputs:
        self._validate_response(response)
        return Outputs._make(
            deserialize_parameters(
                self._output_metadata,
                response.outputs.value,
                f"{self._service_class}.Outputs",
            )
        )

    def _validate_response(self, response: v2_measurement_service_pb2.MeasureResponse) -> None:
        expected_type = "type.googleapis.com/" + ${outputs_message_type | repr}
        actual_type = response.outputs.type_url
        if actual_type != expected_type:
            warnings.warn(
                f"Wrong message type. Expected {expected_type!r} but got {actual_type!r}",
                WrongMessageTypeWarning,
            )
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
    ) -> typing.Generator[${output_type}] :
        """Perform a streaming measurement.

        Returns:
            Stream of measurement outputs.
        """
        parameter_values = [${measure_api_parameters}]
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

    def register_pin_map(self, pin_map_path: pathlib.Path) -> None:
        """Registers the pin map with the pin map service.

        Args:
            pin_map_path: Absolute path of the pin map file.
        """
        pin_map_id = self._get_pin_map_client().update_pin_map(pin_map_path)
        self._pin_map_context = self._pin_map_context._replace(pin_map_id=pin_map_id)

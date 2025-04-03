from __future__ import annotations

import logging
from typing import Callable

import grpc
from deprecation import deprecated
from google.protobuf import descriptor_pool
from grpc.framework.foundation import logging_pool

from ni_measurement_plugin_sdk_service._internal.grpc_servicer import (
    MeasurementServiceServicerV1,
    MeasurementServiceServicerV2,
)
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import (
    ParameterMetadata,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    create_file_descriptor,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient, ServiceLocation
from ni_measurement_plugin_sdk_service.grpc.loggers import ServerLogger
from ni_measurement_plugin_sdk_service.measurement.info import (
    MeasurementInfo,
    ServiceInfo,
)

_logger = logging.getLogger(__name__)
_V1_INTERFACE = "ni.measurementlink.measurement.v1.MeasurementService"
_V2_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


class GrpcService:
    """Manages the gRPC server lifetime and registration."""

    def __init__(self, discovery_client: DiscoveryClient | None = None) -> None:
        """Initialize the service."""
        self._discovery_client = discovery_client or DiscoveryClient()
        self._server: grpc.Server | None = None
        self._service_location: ServiceLocation | None = None
        self._registration_id = ""

    @property
    @deprecated(
        deprecated_in="1.3.0-dev0",
        details="This property should not be public and will be removed in a later release.",
    )
    def discovery_client(self) -> DiscoveryClient:
        """Client for accessing the NI Discovery Service."""
        return self._discovery_client

    @property
    @deprecated(
        deprecated_in="1.3.0-dev0",
        details="Use service_location instead.",
    )
    def port(self) -> str:
        """The insecure port."""
        return self.service_location.insecure_port

    @property
    @deprecated(
        deprecated_in="1.3.0-dev0",
        details="This property should not be public and will be removed in a later release.",
    )
    def server(self) -> grpc.Server | None:
        """The gRPC server."""
        return self._server

    @property
    def service_location(self) -> ServiceLocation:
        """The location of the service on the network."""
        if self._service_location is None:
            raise RuntimeError("Measurement service not running")
        return self._service_location

    def start(
        self,
        measurement_info: MeasurementInfo,
        service_info: ServiceInfo,
        configuration_parameter_list: list[ParameterMetadata],
        output_parameter_list: list[ParameterMetadata],
        measure_function: Callable,
        owner: object = None,
    ) -> str:
        """Start the gRPC server and register it with the discovery service.

        Returns:
            The insecure port.
        """
        interceptors: list[grpc.ServerInterceptor] = []
        if ServerLogger.is_enabled():
            interceptors.append(ServerLogger())
        self._server = grpc.server(
            logging_pool.pool(max_workers=10),
            interceptors=interceptors,
            options=[
                ("grpc.max_receive_message_length", -1),
                ("grpc.max_send_message_length", -1),
            ],
        )
        create_file_descriptor(
            service_name=service_info.service_class,
            output_metadata=output_parameter_list,
            input_metadata=configuration_parameter_list,
            pool=descriptor_pool.Default(),
        )
        for interface in service_info.provided_interfaces:
            if interface == _V1_INTERFACE:
                servicer_v1 = MeasurementServiceServicerV1(
                    measurement_info,
                    configuration_parameter_list,
                    output_parameter_list,
                    measure_function,
                    owner,
                    service_info,
                )
                v1_measurement_service_pb2_grpc.add_MeasurementServiceServicer_to_server(
                    servicer_v1, self._server
                )
            elif interface == _V2_INTERFACE:
                servicer_v2 = MeasurementServiceServicerV2(
                    measurement_info,
                    configuration_parameter_list,
                    output_parameter_list,
                    measure_function,
                    owner,
                    service_info,
                )
                v2_measurement_service_pb2_grpc.add_MeasurementServiceServicer_to_server(
                    servicer_v2, self._server
                )
            else:
                raise ValueError(
                    f"Unknown interface was provided in the .serviceconfig file: {interface}"
                )
        host = "[::1]"
        port = str(self._server.add_insecure_port(f"{host}:0"))
        address = f"http://{host}:{port}"
        self._server.start()
        _logger.info("Measurement service listening on: %s", address)

        self._service_location = ServiceLocation("localhost", port, "")
        self._registration_id = self._discovery_client.register_service(
            service_info, self.service_location
        )
        return port

    def stop(self) -> None:
        """Unregister and stop the gRPC server."""
        if self._registration_id:
            self._discovery_client.unregister_service(self._registration_id)
        if self._server is not None:
            self._server.stop(5)

        self._registration_id = ""
        self._server = None
        self._service_location = None
        _logger.info("Measurement service closed.")

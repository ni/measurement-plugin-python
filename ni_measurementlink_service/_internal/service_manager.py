import logging
from typing import Callable, List, Optional

import grpc
from grpc.framework.foundation import logging_pool

from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.grpc_servicer import (
    MeasurementServiceServicerV1,
    MeasurementServiceServicerV2,
)
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._loggers import ServerLogger
from ni_measurementlink_service.measurement.info import MeasurementInfo, ServiceInfo

_logger = logging.getLogger(__name__)
_V1_INTERFACE = "ni.measurementlink.measurement.v1.MeasurementService"
_V2_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


class GrpcService:
    """Class that manages hosting the measurement as service and closing service.

    Attributes
    ----------
        discovery_client (DiscoveryClient, optional): Instance of Discovery Client.
        Defaults to None.

    """

    def __init__(self, discovery_client: Optional[DiscoveryClient] = None) -> None:
        """Initialize Service Manager.

        Args:
            discovery_client (DiscoveryClient, optional): Instance of Discovery Client.
            Defaults to None.

            servicer(MeasurementServiceServicer): The gRPC implementation class of the service.
            Used in tests.

            port(str) : The port number of the hosted service.Used in Tests.

        """
        self.discovery_client = discovery_client or DiscoveryClient()

    def start(
        self,
        measurement_info: MeasurementInfo,
        service_info: ServiceInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
    ) -> str:
        """Host a gRPC service with the registered measurement method.

        Args:
        ----
            measurement_info (MeasurementInfo): Measurement info

            service_info (ServiceInfo): Service info

            configuration_parameter_list (List): List of configuration parameters.

            output_parameter_list (List): List of output parameters.

            measure_function (Callable): Registered measurement function.

        Returns
        -------
            int: The port number of the server

        """
        interceptors: List[grpc.ServerInterceptor] = []
        if ServerLogger.is_enabled():
            interceptors.append(ServerLogger())
        self.server = grpc.server(
            logging_pool.pool(max_workers=10),
            interceptors=interceptors,
            options=[
                ("grpc.max_receive_message_length", -1),
                ("grpc.max_send_message_length", -1),
            ],
        )
        for interface in service_info.provided_interfaces:
            if interface == _V1_INTERFACE:
                servicer_v1 = MeasurementServiceServicerV1(
                    measurement_info,
                    configuration_parameter_list,
                    output_parameter_list,
                    measure_function,
                )
                v1_measurement_service_pb2_grpc.add_MeasurementServiceServicer_to_server(
                    servicer_v1, self.server
                )
            elif interface == _V2_INTERFACE:
                servicer_v2 = MeasurementServiceServicerV2(
                    measurement_info,
                    configuration_parameter_list,
                    output_parameter_list,
                    measure_function,
                )
                v2_measurement_service_pb2_grpc.add_MeasurementServiceServicer_to_server(
                    servicer_v2, self.server
                )
            else:
                raise ValueError(
                    f"Unknown interface was provided in the .serviceconfig file: {interface}"
                )
        port = str(self.server.add_insecure_port("[::]:0"))
        self.server.start()
        _logger.info("Measurement service hosted on port: %s", port)
        self.discovery_client.register_measurement_service(port, service_info, measurement_info)

        self.port = port
        return port

    def stop(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        self.discovery_client.unregister_service()
        self.server.stop(5)
        _logger.info("Measurement service closed.")

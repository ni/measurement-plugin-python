import logging
from typing import Callable, List

import grpc
from grpc.framework.foundation import logging_pool

from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.grpc_servicer import (
    MeasurementServiceServicer,
)
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.info import MeasurementInfo, ServiceInfo

_logger = logging.getLogger(__name__)


class GrpcService:
    """Class that manages hosting the measurement as service and closing service.

    Attributes
    ----------
        discovery_client (DiscoveryClient, optional): Instance of Discovery Client.
        Defaults to None.

    """

    def __init__(self, discovery_client: DiscoveryClient = None) -> None:
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
        self.server = grpc.server(
            logging_pool.pool(max_workers=10),
            options=[
                ("grpc.max_receive_message_length", -1),
                ("grpc.max_send_message_length", -1),
            ],
        )
        self.servicer = MeasurementServiceServicer(
            measurement_info,
            configuration_parameter_list,
            output_parameter_list,
            measure_function,
        )
        measurement_service_pb2_grpc.add_MeasurementServiceServicer_to_server(
            self.servicer, self.server
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

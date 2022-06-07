# fmt: off
import os
import time
from concurrent import futures
from typing import Callable, List

import grpc

from ni_measurement_service._internal.discovery_client import DiscoveryClient
from ni_measurement_service._internal.grpc_servicer import MeasurementServiceServicer
from ni_measurement_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_service._internal.stubs import Measurement_pb2_grpc
from ni_measurement_service.measurement.info import MeasurementInfo, ServiceInfo
if os.name == "nt":
    from ni_measurement_service._internal.utilities import console_exit_functions

# fmt: on


class ServiceManager:
    """Class that manages hosting the measurement as service and closing service.

    Attributes
    ----------
        measurement_info (MeasurementInfo): Measurement info
        service_info (ServiceInfo): Service info
        configuration_parameter_list (List): List of configuration parameters.
        output_parameter_list (List): List of output parameters.
        measure_function (Callable): Registered measurement function.
        discovery_client (DiscoveryClient, optional): _description_. Defaults to None.

    """

    def __init__(
        self,
        measurement_info: MeasurementInfo,
        service_info: ServiceInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
        discovery_client: DiscoveryClient = None,
    ) -> None:
        """Initialize Service Manager.

        Args:
        ----
            measurement_info (MeasurementInfo): Measurement info
            service_info (ServiceInfo): Service info
            configuration_parameter_list (List): List of configuration parameters.
            output_parameter_list (List): List of output parameters.
            measure_function (Callable): Registered measurement function.
            discovery_client (DiscoveryClient, optional): Instance of Discovery Client.
            Defaults to None.

        """
        self.measurement_info = measurement_info
        self.service_info = service_info
        self.configuration_parameter_list = configuration_parameter_list
        self.output_parameter_list = output_parameter_list
        self.measure_function = measure_function
        self.discovery_client = discovery_client or DiscoveryClient()
        return None

    def serve(self) -> int:
        """Host a gRPC service with the registered measurement method.

        Returns
        -------
            int: The port number of the server

        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        Measurement_pb2_grpc.add_MeasurementServiceServicer_to_server(
            MeasurementServiceServicer(
                self.measurement_info,
                self.configuration_parameter_list,
                self.output_parameter_list,
                self.measure_function,
            ),
            server,
        )
        port = server.add_insecure_port("[::]:0")
        server.start()
        print("Hosted Service at Port:", port)
        self.discovery_client.register_measurement_service(
            port, self.service_info, self.measurement_info.display_name
        )
        if os.name == "nt":
            console_exit_functions.setup_unregister_on_console_close(self.close_service)
        return port

    def close_service(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        self.discovery_client.unregister_service()
        grpc.server.stop(5)
        print("Measurement service exited.")
        time.sleep(2)
        return None

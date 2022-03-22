"""Framework to host measurement service."""
import time
from typing import Any, Callable

from ni_measurement_service._internal import discoveryclient
from ni_measurement_service._internal import grpc_servicer
from ni_measurement_service._internal.parameter import metadata as parameter_metadata
from ni_measurement_service._internal.utilities import consoleexitfunctions
from ni_measurement_service.measurement.info import MeasurementInfo, ServiceInfo, DataType


class MeasurementService:
    """Class the supports registering and hosting a python function as a gRPC service.

    Attributes
    ----------
        measurement_info (info.MeasurementInfo): Measurement info
        service_info(info.ServiceInfo) : Service Info
        configuration_parameter_list (List): List of configuration parameters.
        output_parameter_list (list): List of output parameters.
        measure_function (Callable): Registered measurement function.

    """

    def __init__(self, measurement_info: MeasurementInfo, service_info: ServiceInfo) -> None:
        """Initialize the Measurement Service object with measurement info and service info.

        Args:
        ----
            measurement_info (MeasurementInfo): Measurement Info
            service_info (ServiceInfo): Service Info

        """
        self.measurement_info: MeasurementInfo = measurement_info
        self.service_info: ServiceInfo = service_info
        self.configuration_parameter_list: list = []
        self.output_parameter_list: list = []

    def register_measurement(self, measurement_function: Callable) -> Callable:
        """Register the function as the measurement. Recommended to use as a decorator.

        Args
        ----
            func (Callable): Any Python Function.

        Returns
        -------
            Callable: Python Function.

        """
        self.measure_function = measurement_function
        return measurement_function

    def configuration(self, display_name: str, type: DataType, default_value: Any) -> Callable:
        """Add configuration parameter info for a measurement.Recommended to use as a decorator.

        Args
        ----
            display_name (str): Display name of the configuration.
            type (DataType): Data type of the configuration.
            default_value (Any): Default value of the configuration.

        Returns
        -------
            Callable: Callable that takes in Any Python Function
            and returns the same python function.

        """
        grpc_field_type, repeated = type.value
        parameter = parameter_metadata.ParameterMetadata(
            display_name, grpc_field_type, repeated, default_value
        )
        parameter_metadata.validate_default_value_type(parameter)
        self.configuration_parameter_list.append(parameter)

        def _configuration(func):
            return func

        return _configuration

    def output(self, display_name: str, type: DataType) -> Callable:
        """Add output parameter info for a measurement.Recommended to use as a decorator.

        Args
        ----
            display_name (str): Display name of the output.
            type (DataType): Data type of the output.

        Returns
        -------
            Callable: Callable that takes in Any Python Function and
            returns the same python function.

        """
        grpc_field_type, repeated = type.value
        parameter = parameter_metadata.ParameterMetadata(
            display_name, grpc_field_type, repeated, None
        )
        self.output_parameter_list.append(parameter)

        def _output(func):
            return func

        return _output

    def host_as_grpc_service(self) -> None:
        """Host the registered measurement method as gRPC measurement service.

        Raises
        ------
            Exception: If register measurement methods not available.

        """
        if self.measure_function is None:
            raise Exception("Error, must register measurement method.")
        global server
        server, port = grpc_servicer.serve(
            self.measurement_info,
            self.configuration_parameter_list,
            self.output_parameter_list,
            self.measure_function,
        )
        print("Hosted Service at Port:", port)
        discoveryclient.register_measurement_service(
            port, self.service_info, self.measurement_info.display_name
        )
        consoleexitfunctions.setup_unregister_on_console_close(self.close_service)
        return None

    def close_service(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        discoveryclient.unregister_service()
        server.stop(5)
        print("Measurement service exited.")
        time.sleep(2)
        return None

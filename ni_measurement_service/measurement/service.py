"""Framework to host measurement service."""

from __future__ import annotations

from typing import Any, Dict
from typing import Callable

from ni_measurement_service._internal import grpc_servicer
from ni_measurement_service._internal.discovery_client import DiscoveryClient
from ni_measurement_service._internal.parameter import metadata as parameter_metadata
from ni_measurement_service._internal.service_manager import GrpcService
from ni_measurement_service.measurement.info import DataType
from ni_measurement_service.measurement.info import MeasurementInfo
from ni_measurement_service.measurement.info import ServiceInfo


class MeasurementContext:
    """Proxy for the Measurement Service's context-local state."""

    @property
    def grpc_context(self):
        """Get the context for the RPC."""
        return grpc_servicer.measurement_service_context.get().grpc_context

    @property
    def pin_map_context(self):
        """Get the pin map context for the RPC."""
        return grpc_servicer.measurement_service_context.get().pin_map_context

    def add_cancel_callback(self, cancel_callback: Callable):
        """Add a callback which is invoked when the RPC is canceled."""
        grpc_servicer.measurement_service_context.get().add_cancel_callback(cancel_callback)

    def cancel(self):
        """Cancel the RPC."""
        grpc_servicer.measurement_service_context.get().cancel()

    @property
    def time_remaining(self):
        """Get the time remaining for the RPC."""
        return grpc_servicer.measurement_service_context.get().time_remaining

    def abort(self, code, details):
        """Aborts the RPC."""
        grpc_servicer.measurement_service_context.get().abort(code, details)


class MeasurementService:
    """Class the supports registering and hosting a python function as a gRPC service.

    Attributes
    ----------
        measurement_info (info.MeasurementInfo): Measurement info

        service_info(info.ServiceInfo) : Service Info

        configuration_parameter_list (List): List of configuration parameters.

        output_parameter_list (list): List of output parameters.

        measure_function (Callable): Registered measurement function.

        context (MeasurementContext): Accessor for context-local state.

        discovery_client (DiscoveryClient): Client for accessing the MeasurementLink discovery
            service.

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
        self.grpc_service = GrpcService()
        self.context: MeasurementContext = MeasurementContext()
        self.discovery_client: DiscoveryClient = self.grpc_service.discovery_client

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

    def configuration(self, display_name: str, type: DataType, default_value: Any, *, instrument_type: str = ""
    ) -> Callable:
        """Add configuration parameter info for a measurement.Recommended to use as a decorator.

        Args
        ----
            display_name (str): Display name of the configuration.

            type (DataType): Data type of the configuration.

            default_value (Any): Default value of the configuration.

            instrument_type (str): Optional.
            Intrument type to be used to show instrument specific values to the configurations.
            This is only supported when configuration type is DataType.Pin.

        Returns
        -------
            Callable: Callable that takes in Any Python Function
            and returns the same python function.

        """
        grpc_field_type, repeated = type.value
        annotations = self._get_annotations(type, instrument_type)
        parameter = parameter_metadata.ParameterMetadata(
            display_name, grpc_field_type, repeated, default_value, annotations
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
            display_name, grpc_field_type, repeated, default_value=None, annotations={}
        )
        self.output_parameter_list.append(parameter)

        def _output(func):
            return func

        return _output

    def host_service(self) -> MeasurementService:
        """Host the registered measurement method as gRPC measurement service.

        Returns
        -------
            MeasurementService: Context manager that can be used with a with-statement to close
            the service.

        Raises
        ------
            Exception: If register measurement methods not available.

        """
        if self.measure_function is None:
            raise Exception("Error, must register measurement method.")
        self.grpc_service.start(
            self.measurement_info,
            self.service_info,
            self.configuration_parameter_list,
            self.output_parameter_list,
            self.measure_function,
        )
        return self

    def _get_annotations(self, type: DataType, instrument_type: str) -> Dict[str, str]:
        annotations = {}
        if type == DataType.Pin:
            annotations["ni/type_specialization"] = "pin"

            if instrument_type != "" or instrument_type is not None:
                annotations["ni/pin.instrument_type"] = instrument_type

        return annotations

    def close_service(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        self.grpc_service.stop()

    def __enter__(self) -> MeasurementService:
        """Enter the runtime context related to the measurement service."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to the measurement service."""
        self.close_service()

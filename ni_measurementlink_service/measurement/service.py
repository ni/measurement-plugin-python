"""Framework to host measurement service."""

from __future__ import annotations

import json
from os import path
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, TypeVar

import grpc

from ni_measurementlink_service._internal import grpc_servicer
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.parameter import (
    metadata as parameter_metadata,
)
from ni_measurementlink_service._internal.service_manager import GrpcService
from ni_measurementlink_service.measurement.info import (
    DataType,
    MeasurementInfo,
    ServiceInfo,
    TypeSpecialization,
)


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


# Eventually, these can be replaced with typing.Self (Python >= 3.11).
_TGrpcChannelPool = TypeVar("_TGrpcChannelPool", bound="GrpcChannelPool")
_TMeasurementService = TypeVar("_TMeasurementService", bound="MeasurementService")


class GrpcChannelPool(object):
    """Class that manages gRPC channel lifetimes."""

    def __init__(self):
        """Initialize the GrpcChannelPool object."""
        self._lock: Lock = Lock()
        self._channel_cache: Dict[str, grpc.Channel] = {}

    def __enter__(self: _TGrpcChannelPool) -> _TGrpcChannelPool:
        """Enter the runtime context of the GrpcChannelPool."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context of the GrpcChannelPool."""
        self.close()

    def get_channel(self, target: str) -> grpc.Channel:
        """Return a gRPC channel.

        Args:
            target (str): The server address

        """
        new_channel = None
        with self._lock:
            if target not in self._channel_cache:
                self._lock.release()
                new_channel = grpc.insecure_channel(target)
                self._lock.acquire()
                if target not in self._channel_cache:
                    self._channel_cache[target] = new_channel
                    new_channel = None
            channel = self._channel_cache[target]

        # Close new_channel if it was not stored in _channel_cache.
        if new_channel is not None:
            new_channel.close()

        return channel

    def close(self) -> None:
        """Close channels opened by get_channel()."""
        with self._lock:
            for channel in self._channel_cache.values():
                channel.close()
            self._channel_cache.clear()


class MeasurementService:
    """Class that supports registering and hosting a python function as a gRPC service.

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

        channel_pool (GrpcChannelPool): Pool of gRPC channels used by the service.

    """

    def __init__(
        self,
        service_config_path: Path,
        version: str,
        ui_file_paths: List[Path],
        service_class: str = None,
    ) -> None:
        """Initialize the Measurement Service object.

        Uses the specified .serviceconfig file, version, and UI file paths
        to initialize a Measurement Service object.

        Args:
            service_config_path (Path): Path to the .serviceconfig file.

            version (str): Version of the measurement service.

            ui_file_paths (List[Path]): List of paths to supported UIs.

            service_class (str): The service class from the .serviceconfig to use.
            Default value is None, which will use the first service in the
            .serviceconfig file.

        """
        if not path.exists(service_config_path):
            raise RuntimeError(f"File does not exist. {service_config_path}")

        with open(service_config_path) as service_config_file:
            service_config = json.load(service_config_file)

        if service_class is None:
            service = next(iter(service_config["services"]), None)
        else:
            service = next(
                (s for s in service_config["services"] if s["serviceClass"] == service_class), None
            )
        if not service:
            raise RuntimeError(
                f"Service class '{service_class}' not found in '{service_config_file}'"
            )

        self.measurement_info = MeasurementInfo(
            display_name=service["displayName"],
            version=version,
            ui_file_paths=ui_file_paths,
        )

        self.service_info = ServiceInfo(
            service_class=service["serviceClass"],
            description_url=service["descriptionUrl"],
        )

        self.configuration_parameter_list: list = []
        self.output_parameter_list: list = []
        self.grpc_service = GrpcService()
        self.context: MeasurementContext = MeasurementContext()
        self.discovery_client: DiscoveryClient = self.grpc_service.discovery_client
        self.channel_pool: GrpcChannelPool = GrpcChannelPool()

    def register_measurement(self, measurement_function: Callable) -> Callable:
        """Register a function as the measurement function for a measurement service.

        To declare a measurement function, use this idiom:

        ```
        @measurement_service.register_measurement
        @measurement_service.configuration("Configuration 1", ...)
        @measurement_service.configuration("Configuration 2", ...)
        @measurement_service.output("Output 1", ...)
        @measurement_service.output("Output 2", ...)
        def measure(configuration1, configuration2):
            ...
            return (output1, output2)
        ```

        See also: :func:`.configuration`, :func:`.output`
        """
        self.measure_function = measurement_function
        return measurement_function

    def configuration(
        self, display_name: str, type: DataType, default_value: Any, *, instrument_type: str = ""
    ) -> Callable:
        """Add a configuration parameter to a measurement function.

        This decorator maps the measurement service's configuration parameters
        to Python positional parameters. To add multiple configuration parameters
        to the same measurement function, use this decorator multiple times.
        The order of decorator calls must match the order of positional parameters.

        See also: :func:`.register_measurement`

        Args
        ----
            display_name (str): Display name of the configuration.

            type (DataType): Data type of the configuration.

            default_value (Any): Default value of the configuration.

            instrument_type (str): Optional.
            Filter pins by instrument type. This is only supported when configuration type
            is DataType.Pin. Pin maps have built in instrument definitions using the
            NI driver based instrument type ids. These can be found as constants
            in `nims.session_management`. For example, for an NI DCPower instrument
            the instrument type is `nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER`.
            For custom instruments the user defined instrument type id is defined in the
            pin map file.

        Returns
        -------
            Callable: Callable that takes in Any Python Function
            and returns the same python function.

        """
        grpc_field_type, repeated, type_specialization = type.value
        annotations = self._get_annotations(type_specialization, instrument_type)
        parameter = parameter_metadata.ParameterMetadata(
            display_name, grpc_field_type, repeated, default_value, annotations
        )
        parameter_metadata.validate_default_value_type(parameter)
        self.configuration_parameter_list.append(parameter)

        def _configuration(func):
            return func

        return _configuration

    def output(self, display_name: str, type: DataType) -> Callable:
        """Add a output parameter to a measurement function.

        This decorator maps the measurement service's output parameters to
        the elements of the tuple returned by the measurement function.
        To add multiple output parameters to the same measurement function,
        use this decorator multiple times.
        The order of decorator calls must match the order of elements
        returned by the measurement fuction.

        See also: :func:`.register_measurement`

        Args
        ----
            display_name (str): Display name of the output.

            type (DataType): Data type of the output.

        Returns
        -------
            Callable: Callable that takes in Any Python Function and
            returns the same python function.

        """
        grpc_field_type, repeated, type_specialization = type.value
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

    def _get_annotations(
        self, type_specialization: TypeSpecialization, instrument_type: str
    ) -> Dict[str, str]:
        annotations: Dict[str, str] = {}
        if type_specialization == TypeSpecialization.NoType:
            return annotations

        annotations["ni/type_specialization"] = type_specialization.value
        if type_specialization == TypeSpecialization.Pin:
            if instrument_type != "" or instrument_type is not None:
                annotations["ni/pin.instrument_type"] = instrument_type

        return annotations

    def close_service(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        self.grpc_service.stop()
        self.channel_pool.close()

    def __enter__(self: _TMeasurementService) -> _TMeasurementService:
        """Enter the runtime context related to the measurement service."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to the measurement service."""
        self.close_service()

    def get_channel(self, provided_interface: str, service_class: str = "") -> grpc.Channel:
        """Return gRPC channel to specified service.

        Args
        ----
            provided_interface (str): The gRPC Full Name of the service.

            service_class (str): The service "class" that should be matched.

        Returns
        -------
            grpc.Channel: A channel to the gRPC service.

        Raises
        ------
            Exception: If service_class is not specified and there is more than one matching service
                registered.

        """
        service_location = self.grpc_service.discovery_client.resolve_service(
            provided_interface, service_class
        )

        return self.channel_pool.get_channel(target=service_location.insecure_address)

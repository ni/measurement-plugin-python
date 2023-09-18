"""Framework to host measurement service."""

from __future__ import annotations

import json
import sys
from enum import Enum, EnumMeta
from os import path
from pathlib import Path
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)

import grpc
from google.protobuf.descriptor import EnumDescriptor

from ni_measurementlink_service import _datatypeinfo
from ni_measurementlink_service._channelpool import (  # re-export
    GrpcChannelPool as GrpcChannelPool,
)
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
from ni_measurementlink_service.session_management import PinMapContext

if TYPE_CHECKING:
    from google.protobuf.internal.enum_type_wrapper import _EnumTypeWrapper

    if sys.version_info >= (3, 10):
        from typing import TypeGuard
    else:
        from typing_extensions import TypeGuard

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    SupportedEnumType = Union[Type[Enum], _EnumTypeWrapper]


class MeasurementContext:
    """Proxy for the Measurement Service's context-local state."""

    @property
    def grpc_context(self) -> grpc.ServicerContext:
        """Get the context for the RPC."""
        return grpc_servicer.measurement_service_context.get().grpc_context

    @property
    def pin_map_context(self) -> PinMapContext:
        """Get the pin map context for the RPC."""
        return grpc_servicer.measurement_service_context.get().pin_map_context

    def add_cancel_callback(self, cancel_callback: Callable[[], None]) -> None:
        """Add a callback which is invoked when the RPC is canceled."""
        grpc_servicer.measurement_service_context.get().add_cancel_callback(cancel_callback)

    def cancel(self) -> None:
        """Cancel the RPC."""
        grpc_servicer.measurement_service_context.get().cancel()

    @property
    def time_remaining(self) -> float:
        """Get the time remaining for the RPC."""
        return grpc_servicer.measurement_service_context.get().time_remaining

    def abort(self, code: grpc.StatusCode, details: str) -> None:
        """Aborts the RPC."""
        grpc_servicer.measurement_service_context.get().abort(code, details)


_F = TypeVar("_F", bound=Callable)


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
        service_class: Optional[str] = None,
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

        def convert_value_to_str(value: object) -> str:
            if isinstance(value, str):
                return value
            return json.dumps(value, separators=(",", ":"))

        service_annotations_string = {
            key: convert_value_to_str(value)
            for key, value in service.get("annotations", {}).items()
        }

        self.service_info = ServiceInfo(
            service_class=service["serviceClass"],
            description_url=service["descriptionUrl"],
            provided_interfaces=service["providedInterfaces"],
            annotations=service_annotations_string,
        )

        self.configuration_parameter_list: List[Any] = []
        self.output_parameter_list: List[Any] = []
        self.grpc_service = GrpcService()
        self.context: MeasurementContext = MeasurementContext()
        self.channel_pool: GrpcChannelPool = GrpcChannelPool()
        self.discovery_client: DiscoveryClient = DiscoveryClient()

    def register_measurement(self, measurement_function: _F) -> _F:
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
        self,
        display_name: str,
        type: DataType,
        default_value: Any,
        *,
        instrument_type: str = "",
        enum_type: Optional[SupportedEnumType] = None,
    ) -> Callable[[_F], _F]:
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

            instrument_type (Optional[str]):
            Filter pins by instrument type. This is only supported when configuration type
            is DataType.Pin. Pin maps have built in instrument definitions using the
            NI driver based instrument type ids. These can be found as constants
            in `nims.session_management`. For example, for an NI DCPower instrument
            the instrument type is `nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER`.
            For custom instruments the user defined instrument type id is defined in the
            pin map file.

            enum_type (Optional[SupportedEnumType]):
            Defines the enum type associated with this configuration parameter. This is only
            supported when configuration type is DataType.Enum or DataType.EnumArray1D.

        Returns
        -------
            Callable: Callable that takes in Any Python Function
            and returns the same python function.

        """
        data_type_info = _datatypeinfo.get_type_info(type)
        annotations = self._make_annotations_dict(
            data_type_info.type_specialization, instrument_type=instrument_type, enum_type=enum_type
        )
        parameter = parameter_metadata.ParameterMetadata(
            display_name,
            data_type_info.grpc_field_type,
            data_type_info.repeated,
            default_value,
            annotations,
            data_type_info.message_type,
        )
        parameter_metadata.validate_default_value_type(parameter)
        self.configuration_parameter_list.append(parameter)

        def _configuration(func: _F) -> _F:
            return func

        return _configuration

    def output(
        self,
        display_name: str,
        type: DataType,
        *,
        enum_type: Optional[SupportedEnumType] = None,
    ) -> Callable[[_F], _F]:
        """Add an output parameter to a measurement function.

        This decorator maps the measurement service's output parameters to
        the elements of the tuple returned by the measurement function.
        To add multiple output parameters to the same measurement function,
        use this decorator multiple times.
        The order of decorator calls must match the order of elements
        returned by the measurement function.

        See also: :func:`.register_measurement`

        Args
        ----
            display_name (str): Display name of the output.

            type (DataType): Data type of the output.

            enum_type (Optional[SupportedEnumType]:
            Defines the enum type associated with this configuration parameter. This is only
            supported when configuration type is DataType.Enum or DataType.EnumArray1D.

        Returns
        -------
            Callable: Callable that takes in Any Python Function and
            returns the same python function.

        """
        data_type_info = _datatypeinfo.get_type_info(type)
        annotations = self._make_annotations_dict(
            data_type_info.type_specialization, enum_type=enum_type
        )
        parameter = parameter_metadata.ParameterMetadata(
            display_name,
            data_type_info.grpc_field_type,
            data_type_info.repeated,
            None,
            annotations,
            data_type_info.message_type,
        )
        self.output_parameter_list.append(parameter)

        def _output(func: _F) -> _F:
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

    def _make_annotations_dict(
        self,
        type_specialization: TypeSpecialization,
        *,
        instrument_type: str = "",
        enum_type: Optional[SupportedEnumType] = None,
    ) -> Dict[str, str]:
        annotations: Dict[str, str] = {}
        if type_specialization == TypeSpecialization.NoType:
            return annotations

        annotations["ni/type_specialization"] = type_specialization.value
        if type_specialization == TypeSpecialization.Pin:
            if instrument_type != "" or instrument_type is not None:
                annotations["ni/pin.instrument_type"] = instrument_type
        if type_specialization == TypeSpecialization.Enum:
            if enum_type is not None:
                annotations["ni/enum.values"] = self._enum_to_annotations_value(enum_type)
            else:
                raise ValueError("enum_type is required for enum parameters.")

        return annotations

    def _enum_to_annotations_value(self, enum_type: SupportedEnumType) -> str:
        enum_values = {}
        # For protobuf enums, enum_type is an instance of EnumTypeWrapper at run time, so passing
        # it to issubclass() would raise an error.
        if self._is_protobuf_enum(enum_type):
            if 0 not in enum_type.values():
                raise ValueError("The enum does not have a value for 0.")
            for name, value in enum_type.items():
                enum_values[name] = value
        elif isinstance(enum_type, EnumMeta):
            if not any(member.value == 0 for member in enum_type):
                raise ValueError("The enum does not have a value for 0.")
            for member in enum_type:
                enum_values[member.name] = member.value
        return json.dumps(enum_values)

    def _is_protobuf_enum(self, enum_type: SupportedEnumType) -> TypeGuard[_EnumTypeWrapper]:
        # Use EnumDescriptor to check for protobuf enums at run time without using
        # google.protobuf.internal.
        return isinstance(getattr(enum_type, "DESCRIPTOR", None), EnumDescriptor)

    def close_service(self) -> None:
        """Close the Service after un-registering with discovery service and cleanups."""
        self.grpc_service.stop()
        self.channel_pool.close()

    def __enter__(self: Self) -> Self:
        """Enter the runtime context related to the measurement service."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        """Exit the runtime context related to the measurement service."""
        self.close_service()
        return False

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

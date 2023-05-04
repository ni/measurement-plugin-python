"""Helper classes and functions for MeasurementLink examples."""

import contextlib
import logging
import pathlib
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple, TypeVar

import click
import grpc

from ni_measurementlink_service import session_management
import ni_measurementlink_service as nims
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pinmap.v1 import (
    pin_map_service_pb2,
    pin_map_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import GrpcChannelPool, MeasurementService


class ServiceOptions(NamedTuple):
    """Service options specified on the command line."""

    use_grpc_device: bool = False
    grpc_device_address: str = ""

    use_simulation: bool = False


def get_service_options(**kwargs) -> ServiceOptions:
    """Get service options from keyword arguments."""
    return ServiceOptions(
        use_grpc_device=kwargs.get("use_grpc_device", False),
        grpc_device_address=kwargs.get("grpc_device_address", ""),
        use_simulation=kwargs.get("use_simulation", False),
    )


T = TypeVar("T")


def str_to_enum(mapping: Dict[str, T], value: str) -> T:
    """Convert a string to an enum (with improved error reporting)."""
    try:
        return mapping[value]
    except KeyError as e:
        logging.error("Unsupported enum value %s", value)
        raise grpc.RpcError(
            grpc.StatusCode.INVALID_ARGUMENT,
            f'Unsupported enum value "{value}"',
        ) from e


class PinMapClient(object):
    """Class that communicates with the pin map service."""

    def __init__(self, *, grpc_channel: grpc.Channel):
        """Initialize pin map client."""
        self._client: pin_map_service_pb2_grpc.PinMapServiceStub = (
            pin_map_service_pb2_grpc.PinMapServiceStub(grpc_channel)
        )

    def update_pin_map(self, pin_map_path: str) -> str:
        """Update registered pin map contents.

        Create and register a pin map if a pin map resource for the specified pin map id is not
        found.

        Args:
            pin_map_path: The file path of the pin map to register as a pin map resource.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        pin_map_path_obj = pathlib.Path(pin_map_path)
        # By convention, the pin map id is the .pinmap file path.
        request = pin_map_service_pb2.UpdatePinMapFromXmlRequest(
            pin_map_id=pin_map_path, pin_map_xml=pin_map_path_obj.read_text(encoding="utf-8")
        )
        response: pin_map_service_pb2.PinMap = self._client.UpdatePinMapFromXml(request)
        return response.pin_map_id


class GrpcChannelPoolHelper(GrpcChannelPool):
    """Class that manages gRPC channel lifetimes."""

    def __init__(self):
        """Initialize the GrpcChannelPool object."""
        super().__init__()
        self._discovery_client = DiscoveryClient()

    @property
    def pin_map_channel(self) -> grpc.Channel:
        """Return gRPC channel to pin map service."""
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface="ni.measurementlink.pinmap.v1.PinMapService",
                service_class="ni.measurementlink.pinmap.v1.PinMapService",
            ).insecure_address
        )

    @property
    def session_management_channel(self) -> grpc.Channel:
        """Return gRPC channel to session management service."""
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface=session_management.GRPC_SERVICE_INTERFACE_NAME,
                service_class=session_management.GRPC_SERVICE_CLASS,
            ).insecure_address
        )

    def get_grpc_device_channel(self, provided_interface: str) -> grpc.Channel:
        """Return gRPC channel to specified NI gRPC Device service.

        Args:
            provided_interface (str): The gRPC Full Name of the service.

        """
        return self.get_channel(
            self._discovery_client.resolve_service(
                provided_interface=provided_interface,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            ).insecure_address
        )


class TestStandSupport(object):
    """Class that communicates with TestStand."""

    def __init__(self, sequence_context: Any) -> None:
        """Initialize the TestStandSupport object.

        Args:
            sequence_context:
                The SequenceContext COM object from the TestStand sequence execution.
                (Dynamically typed.)
        """
        self._sequence_context = sequence_context

    def get_active_pin_map_id(self) -> str:
        """Get the active pin map id from the NI.MeasurementLink.PinMapId temporary global variable.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        return self._sequence_context.Engine.TemporaryGlobals.GetValString(
            "NI.MeasurementLink.PinMapId", 0x0
        )

    def set_active_pin_map_id(self, pin_map_id: str) -> None:
        """Set the NI.MeasurementLink.PinMapId temporary global variable to the specified id.

        Args:
            pin_map_id:
                The resource id of the pin map that is registered to the pin map service.
        """
        self._sequence_context.Engine.TemporaryGlobals.SetValString(
            "NI.MeasurementLink.PinMapId", 0x1, pin_map_id
        )

    def resolve_file_path(self, file_path: str) -> str:
        """Resolve the absolute path to a file using the TestStand search directories.

        Args:
            file_path:
                An absolute or relative path to the file. If this is a relative path, this function
                searches the TestStand search directories for it.

        Returns:
            The absolute path to the file.
        """
        if pathlib.Path(file_path).is_absolute():
            return file_path
        (_, absolute_path, _, _, user_canceled) = self._sequence_context.Engine.FindFileEx(
            fileToFind=file_path,
            absolutePath=None,
            srchDirType=None,
            searchDirectoryIndex=None,
            userCancelled=None,  # Must match spelling used by TestStand
            searchContext=self._sequence_context.SequenceFile,
        )
        if user_canceled:
            raise RuntimeError("File lookup canceled by user.")
        return absolute_path


def configure_logging(verbosity: int):
    """Configure logging for this process."""
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)


F = TypeVar("F", bound=Callable)


def verbosity_option(func: F) -> F:
    """Decorator for --verbose command line option."""
    return click.option(
        "-v",
        "--verbose",
        "verbosity",
        count=True,
        help="Enable verbose logging. Repeat to increase verbosity.",
    )(func)


def grpc_device_options(func: F) -> F:
    """Decorator for NI gRPC Device Server command line options."""
    use_grpc_device_option = click.option(
        "--use-grpc-device/--no-use-grpc-device",
        default=True,
        is_flag=True,
        help="Use the NI gRPC Device Server.",
    )
    grpc_device_address_option = click.option(
        "--grpc-device-address",
        default="",
        help="NI gRPC Device Server address (e.g. localhost:31763). If unspecified, use the discovery service to resolve the address.",
    )
    return grpc_device_address_option(use_grpc_device_option(func))


def use_simulation_option(default: bool) -> Callable[[F], F]:
    """Decorator for --use-simulation command line option."""
    return click.option(
        "--use-simulation/--no-use-simulation",
        default=default,
        is_flag=True,
        help="Use simulated instruments.",
    )


def create_driver_session(
    measurement_service: MeasurementService,
    pin_names: Iterable[str],
    instrument_type_module: Any,
    service_options: ServiceOptions,
    instrument_type_id: str
) -> Tuple[Any, List[session_management.SessionInformation]]:
    """Create and register driver sessions."""
    session_management_client = nims.session_management.Client(
            grpc_channel=measurement_service.get_channel(
                provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
                service_class=nims.session_management.GRPC_SERVICE_CLASS,
            )
        )
    
    with contextlib.ExitStack() as stack:            
        reservation = stack.enter_context(reserve_session(
            session_management_client,
            measurement_service.context.pin_map_context,
            instrument_type_id,
            pin_names,
        ))

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        # Leave session open.
        session = stack.enter_context(create_session(
            reservation.session_info[0],
            instrument_type_module,
            service_options,
            measurement_service,
        ))

    return (session, reservation.session_info)


def create_session(
    session_info: session_management.SessionInformation,
    instrument_type_module,
    service_options: Optional[ServiceOptions] = None,
    measurement_service: Optional[MeasurementService] = None,
) -> Any:
    session_kwargs = {}
    if service_options is None:
        with GrpcChannelPoolHelper() as grpc_channel_pool:
            grpc_options = instrument_type_module.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(
                        instrument_type_module.GRPC_SERVICE_INTERFACE_NAME
                    ),
                    session_name=session_info.session_name,
                    initialization_behavior=instrument_type_module.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )
            return instrument_type_module.Session(resource_name=session_info.resource_name, grpc_options=grpc_options)
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=instrument_type_module.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["grpc_options"] = instrument_type_module.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=instrument_type_module.SessionInitializationBehavior.AUTO,
        )
    return instrument_type_module.Session(resource_name=session_info.resource_name, **session_kwargs)


def reserve_session(
    session_management_client: session_management.Client,
    pin_map_context: session_management.PinMapContext,
    instrument_type_id: str,
    pin_names: Optional[Iterable[str]] = None,
) -> session_management.Reservation:
    return session_management_client.reserve_sessions(
            context=pin_map_context,
            pin_or_relay_names=pin_names,
            instrument_type_id=instrument_type_id,
            # If another measurement is using the session, wait for it to complete.
            # Specify a timeout to aid in debugging missed unreserve calls.
            # Long measurements may require a longer timeout.
            timeout=60,
        )

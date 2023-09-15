"""Helper classes and functions for MeasurementLink examples."""

import logging
import pathlib
import types
from typing import (
    Any,
    Callable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import click
import grpc
import ni_measurementlink_service as nims
from ni_measurementlink_service import session_management
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pinmap.v1 import (
    pin_map_service_pb2,
    pin_map_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import (
    GrpcChannelPool,
    MeasurementService,
)


class ServiceOptions(NamedTuple):
    """Service options specified on the command line."""

    use_grpc_device: bool = False
    grpc_device_address: str = ""

    use_simulation: bool = False


def get_service_options(**kwargs: Any) -> ServiceOptions:
    """Get service options from keyword arguments."""
    return ServiceOptions(
        use_grpc_device=kwargs.get("use_grpc_device", False),
        grpc_device_address=kwargs.get("grpc_device_address", ""),
        use_simulation=kwargs.get("use_simulation", False),
    )


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

    def __init__(self) -> None:
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


def configure_logging(verbosity: int) -> None:
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


def get_grpc_device_channel(
    measurement_service: MeasurementService,
    driver_module: types.ModuleType,
    service_options: ServiceOptions,
) -> Optional[grpc.Channel]:
    """Returns driver specific grpc device channel."""
    if service_options.use_grpc_device:
        if service_options.grpc_device_address:
            return measurement_service.channel_pool.get_channel(service_options.grpc_device_address)

        return measurement_service.get_channel(
            provided_interface=getattr(driver_module, "GRPC_SERVICE_INTERFACE_NAME"),
            service_class="ni.measurementlink.v1.grpcdeviceserver",
        )
    return None


def create_session_management_client(
    measurement_service: MeasurementService,
) -> nims.session_management.Client:
    """Return created session management client."""
    return nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )


def get_session_and_channel_for_pin(
    session_info: List[nims.session_management.SessionInformation],
    pin: str,
    site: Optional[int] = None,
) -> Tuple[int, List[str]]:
    """Returns the session information based on the given pin names."""
    session_and_channel_info = get_sessions_and_channels_for_pins(
        session_info=session_info, pins=[pin], site=site
    )

    if len(session_and_channel_info) != 1:
        raise ValueError(f"Unsupported number of sessions for {pin}: {len(session_info)}")
    return session_and_channel_info[0]


def get_sessions_and_channels_for_pins(
    session_info: List[nims.session_management.SessionInformation],
    pins: Union[str, List[str]],
    site: Optional[int] = None,
) -> List[Tuple[int, List[str]]]:
    """Returns the session information based on the given pin names."""
    pin_names = [pins] if isinstance(pins, str) else pins
    session_and_channel_info = []
    for session_index, session_details in enumerate(session_info):
        channel_list = [
            mapping.channel
            for mapping in session_details.channel_mappings
            if mapping.pin_or_relay_name in pin_names and (site is None or mapping.site == site)
        ]
        if len(channel_list) != 0:
            session_and_channel_info.append((session_index, channel_list))

    if len(session_and_channel_info) == 0:
        raise KeyError(f"Pin(s) {pins} and site {site} not found")

    return session_and_channel_info

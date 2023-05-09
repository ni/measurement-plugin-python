"""nidcpower Helper classes and functions for MeasurementLink examples."""

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar
import click

import grpc
import ni_measurementlink_service as nims
from ni_measurementlink_service import session_management
from ni_measurementlink_service.measurement.service import MeasurementService
from _helpers import GrpcChannelPoolHelper

# To use a physical NI SMU instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True

def create_driver_session(
    measurement_service: MeasurementService,
    pin_names: Iterable[str],
    instrument_type_module: Any,
    instrument_type_id: str,
) -> Tuple[Any, List[session_management.SessionInformation]]:
    """Create and reserve driver sessions."""
    session_management_client = nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )

    with reserve_session(
        session_management_client,
        measurement_service.context.pin_map_context,
        instrument_type_id,
        timeout=60,
        pin_names=pin_names,
    ) as reservation:
        with GrpcChannelPoolHelper as grpc_channel_pool:
            if len(reservation.session_info) != 1:
                measurement_service.context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    f"Unsupported number of sessions: {len(reservation.session_info)}",
                )

            # Leave session open.
            session = create_session(
                reservation.session_info[0],
                instrument_type_module,
                grpc_channel_pool
            )

    return (session, reservation.session_info)


def create_session(
    session_info: session_management.SessionInformation,
    instrument_type_module,
    grpc_channel_pool,
) -> Any:
    """Create driver session based on the instrument type and reserved session."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "4141"}

    session_kwargs: Dict[
        str, Any
    ] = {}  # To support teststand_fixture functions since they dont have service options    

    session_kwargs["grpc_options"] = instrument_type_module.GrpcSessionOptions(
        grpc_channel_pool.get_grpc_device_channel(
            provided_interface=instrument_type_module.GRPC_SERVICE_INTERFACE_NAME,
        ),
        session_name=session_info.session_name,
        initialization_behavior=instrument_type_module.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    )

    return instrument_type_module.Session(
        resource_name=session_info.resource_name, options=options, **session_kwargs
    )


def reserve_session(
    session_management_client: session_management.Client,
    pin_map_context: session_management.PinMapContext,
    instrument_type_id: str,
    timeout: int,
    pin_names: Optional[Iterable[str]] = None,
) -> session_management.Reservation:
    """Reserve the session based on the instrument type id."""
    return session_management_client.reserve_sessions(
        context=pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=instrument_type_id,
        # If another measurement is using the session, wait for it to complete.
        # Specify a timeout to aid in debugging missed unreserve calls.
        # Long measurements may require a longer timeout.
        timeout=timeout,
    )


F = TypeVar("F", bound=Callable)


def use_simulation_option(default: bool) -> Callable[[F], F]:
    """Decorator for --use-simulation command line option."""
    return click.option(
        "--use-simulation/--no-use-simulation",
        default=default,
        is_flag=True,
        help="Use simulated instruments.",
    )
"""nidcpower Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Iterable, Optional

import grpc
import nidcpower

import ni_measurementlink_service as nims

# To use a physical NI SMU instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def create_nidcpower_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: grpc.Channel,
) -> nidcpower.Session:
    """Create driver session based on the instrument type and reserved session."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "4141"}

    session_kwargs: Dict[str, Any] = {}

    session_kwargs["grpc_options"] = nidcpower.GrpcSessionOptions(
        session_grpc_channel,
        session_name=session_info.session_name,
        initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
    )

    return nidcpower.Session(
        resource_name=session_info.resource_name, options=options, **session_kwargs
    )


def reserve_session(
    session_management_client: nims.session_management.Client,
    pin_map_context: nims.session_management.PinMapContext,
    timeout: int,
    pin_names: Optional[Iterable[str]] = None,
) -> nims.session_management.Reservation:
    """Reserve the session based on the instrument type id."""    
    return session_management_client.reserve_sessions(
        context=pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
        # If another measurement is using the session, wait for it to complete.
        # Specify a timeout to aid in debugging missed unreserve calls.
        # Long measurements may require a longer timeout.
        timeout=timeout,
    )


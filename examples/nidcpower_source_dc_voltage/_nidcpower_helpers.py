"""nidcpower Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Iterable, Optional

import grpc
import nidcpower

import ni_measurementlink_service as nims

# To use a physical NI SMU instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: grpc.Channel,
    initialization_behavior: Optional[
        nidcpower.SessionInitializationBehavior
    ] = nidcpower.SessionInitializationBehavior.AUTO,
) -> nidcpower.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "4141"}

    session_kwargs: Dict[str, Any] = {}

    session_kwargs["grpc_options"] = nidcpower.GrpcSessionOptions(
        session_grpc_channel,
        session_name=session_info.session_name,
        initialization_behavior=initialization_behavior,
    )

    return nidcpower.Session(
        resource_name=session_info.resource_name, options=options, **session_kwargs
    )


def reserve_session(
    session_management_client: nims.session_management.Client,
    pin_map_context: nims.session_management.PinMapContext,
    pin_names: Optional[Iterable[str]] = None,
    timeout: Optional[float] = None,
) -> nims.session_management.MultiSessionReservation:
    """Reserve session(s).

    Reserve session(s) for the given pins and returns the
    information needed to create or access the session.
    """
    return session_management_client.reserve_sessions(
        context=pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
        timeout=timeout,
    )

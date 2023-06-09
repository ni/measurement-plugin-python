"""nidcpower Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict

import grpc
import nidcpower

import ni_measurementlink_service as nims

# To use a physical NI SMU instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: grpc.Channel,
    initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
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

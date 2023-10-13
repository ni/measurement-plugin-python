"""nidmm Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Optional

import grpc
import ni_measurementlink_service as nims
import nidmm
from _constants import USE_SIMULATION


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior: nidmm.SessionInitializationBehavior = nidmm.SessionInitializationBehavior.AUTO,
) -> nidmm.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "4081"}

    session_kwargs: Dict[str, Any] = {}

    if session_grpc_channel is not None:
        session_kwargs["grpc_options"] = nidmm.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=initialization_behavior,
        )

    return nidmm.Session(session_info.resource_name, options=options, **session_kwargs)

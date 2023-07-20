"""nidcpower Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Optional

import grpc
import nidcpower

import ni_measurementlink_service as nims


def create_session(
    session_info: nims.session_management.SessionInformation,
    use_simulation: bool,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
) -> nidcpower.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if use_simulation:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "4141"}

    session_kwargs: Dict[str, Any] = {}

    if session_grpc_channel is not None:
        session_kwargs["grpc_options"] = nidcpower.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=initialization_behavior,
        )

    return nidcpower.Session(
        resource_name=session_info.resource_name, options=options, **session_kwargs
    )

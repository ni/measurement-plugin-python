"""niswitch Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Optional

import grpc
import niswitch

import ni_measurementlink_service as nims

USE_SIMULATION = True
"""
To use a physical NI relay driver instrument, set this to False or specify
--no-use-simulation on the command line.
"""


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=niswitch.SessionInitializationBehavior.AUTO,
) -> niswitch.Session:
    """Create driver session based on reserved session and grpc channel."""
    resource_name = session_info.resource_name
    session_kwargs: Dict[str, Any] = {}
    if USE_SIMULATION:
        resource_name = ""
        session_kwargs["simulate"] = True
        session_kwargs["topology"] = "2567/Independent"
    if session_grpc_channel is None:
        session_kwargs["grpc_options"] = niswitch.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=niswitch.SessionInitializationBehavior.AUTO,
        )

    # This uses the topology configured in MAX.
    return niswitch.Session(resource_name, **session_kwargs)

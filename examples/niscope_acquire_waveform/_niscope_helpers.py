"""niscope Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Optional

import grpc
import niscope

import ni_measurementlink_service as nims

# To use a physical NI oscilloscope instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=niscope.SessionInitializationBehavior.AUTO,
) -> niscope.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "5162 (4CH)"}

    session_kwargs: Dict[str, Any] = {}

    if session_grpc_channel is not None:
        session_kwargs["grpc_options"] = niscope.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=niscope.SessionInitializationBehavior.AUTO,
        )

    return niscope.Session(session_info.resource_name, options=options, **session_kwargs)

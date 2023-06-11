"""nifgen Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict, Optional

import grpc
import nifgen

import ni_measurementlink_service as nims

# To use a physical NI waveform generator instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=nifgen.SessionInitializationBehavior.AUTO,
) -> nifgen.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "5423 (2CH)"}

    session_kwargs: Dict[str, Any] = {}
    if session_grpc_channel is not None:
        # Assumption: the pin map specifies one NI-FGEN session per instrument. If the pin map
        # specified an NI-FGEN session per channel, the session name would need to include the
        # channel name(s).
        session_kwargs["grpc_options"] = nifgen.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=initialization_behavior,
        )

    return nifgen.Session(
        session_info.resource_name, session_info.channel_list, options=options, **session_kwargs
    )

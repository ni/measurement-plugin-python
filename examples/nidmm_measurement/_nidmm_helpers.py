"""nidmm Helper classes and functions for MeasurementLink examples."""

from typing import Any, Dict

import grpc
import nidmm

import ni_measurementlink_service as nims

# To use a physical NI-DMM instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


def _create_nidmm_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: grpc.Channel=None,
    initialization_behavior=nidmm.SessionInitializationBehavior.AUTO,
) -> nidmm.Session:
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

"""nidaqmx Helper classes and functions for MeasurementLink examples."""

from typing import Optional

import grpc
import ni_measurementlink_service as nims
import nidaqmx


def create_task(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=nidaqmx.SessionInitializationBehavior.AUTO,
) -> nidaqmx.Task:
    """Create daqmx task based on reserved session and grpc channel."""
    session_kwargs = {}

    if session_grpc_channel is not None:
        session_kwargs["grpc_options"] = nidaqmx.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=initialization_behavior,
        )

    return nidaqmx.Task(new_task_name=session_info.session_name, **session_kwargs)

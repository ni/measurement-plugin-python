"""nidcpower Helper classes and functions for MeasurementLink examples."""

import time
from typing import Any, Dict, Optional

import grpc
import nidcpower

import ni_measurementlink_service as nims

USE_SIMULATION = True
"""
To use a physical NI SMU instrument, set this to False or specify
--no-use-simulation on the command line.
"""
NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933


def create_session(
    session_info: nims.session_management.SessionInformation,
    session_grpc_channel: Optional[grpc.Channel] = None,
    initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
) -> nidcpower.Session:
    """Create driver session based on reserved session and grpc channel."""
    options: Dict[str, Any] = {}
    if USE_SIMULATION:
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


def wait_for_source_complete_event(measurement_service, channels, pending_cancellation):
    deadline = time.time() + measurement_service.context.time_remaining
    while True:
        if time.time() > deadline:
            measurement_service.context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded"
            )
        if pending_cancellation:
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "client requested cancellation"
            )
        try:
            channels.wait_for_event(
                nidcpower.enums.Event.SOURCE_COMPLETE, timeout=0.1
            )
            break
        except nidcpower.errors.DriverError as e:
            """
            There is no native way to support cancellation when taking a DCPower
            measurement. To support cancellation, we will be calling WaitForEvent
            until it succeeds or we have gone past the specified timeout. WaitForEvent
            will throw an exception if it times out, which is why we are catching
            and doing nothing.
            """
            if (
                e.code == NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE
                or e.code == NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE
            ):
                pass
            else:
                raise


def add_cancel_callback(session, measurement_service, pending_cancellation):
    def cancel_callback():
        session_to_abort = session
        if session_to_abort is not None:
            nonlocal pending_cancellation
            pending_cancellation = True
            session_to_abort.abort()
    measurement_service.context.add_cancel_callback(cancel_callback)

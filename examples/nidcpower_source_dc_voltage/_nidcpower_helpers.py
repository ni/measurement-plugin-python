"""nidcpower Helper classes and functions for MeasurementLink examples."""

import functools
from typing import Any, Callable, Dict, Optional

import grpc
import nidcpower

import ni_measurementlink_service as nims
from _helpers import get_grpc_device_channel, ServiceOptions

USE_SIMULATION = True
"""
To use a physical NI SMU instrument, set this to False or specify
--no-use-simulation on the command line.
"""


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


def single_session(measurement_service: nims.MeasurementService, service_options: ServiceOptions, session_info_arg_name: str = "session_info", session_arg_name: str = "session") -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            session_info = kwargs[session_info_arg_name]

            grpc_device_channel = get_grpc_device_channel(
                measurement_service, nidcpower, service_options
            )
            with create_session(session_info, grpc_device_channel) as session:
                kwargs[session_arg_name] = session
                return func(*args, **kwargs)
            
        return wrapper
    
    return decorator
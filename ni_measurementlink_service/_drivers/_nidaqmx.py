from __future__ import annotations

from typing import Any, Dict

import nidaqmx

from ni_measurementlink_service._drivers._grpcdevice import (
    get_insecure_grpc_device_server_channel,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool
from ni_measurementlink_service.session_management._types import (
    SessionInformation,
    SessionInitializationBehavior,
)

_INITIALIZATION_BEHAVIOR = {
    SessionInitializationBehavior.AUTO: nidaqmx.SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: nidaqmx.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: nidaqmx.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: nidaqmx.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: nidaqmx.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
}


class SessionConstructor:
    """Constructs sessions based on SessionInformation."""

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        grpc_channel_pool: GrpcChannelPool,
        initialization_behavior: SessionInitializationBehavior,
    ) -> None:
        """Initialize the session constructor."""
        self._grpc_channel = get_insecure_grpc_device_server_channel(
            discovery_client, grpc_channel_pool, nidaqmx.GRPC_SERVICE_INTERFACE_NAME
        )
        self._initialization_behavior = _INITIALIZATION_BEHAVIOR[initialization_behavior]

    def __call__(self, session_info: SessionInformation) -> nidaqmx.Task:
        """Construct a session object."""
        kwargs: Dict[str, Any] = {}
        if self._grpc_channel:
            kwargs["grpc_options"] = nidaqmx.GrpcSessionOptions(
                grpc_channel=self._grpc_channel,
                session_name=session_info.session_name,
                initialization_behavior=self._initialization_behavior,
            )

        return nidaqmx.Task(
            new_task_name=session_info.session_name,
            **kwargs,
        )

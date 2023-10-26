from __future__ import annotations

from typing import Any, Dict, Optional

import nifgen

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._configuration import NIFGEN_OPTIONS
from ni_measurementlink_service._drivers._grpcdevice import (
    get_insecure_grpc_device_channel,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.session_management._types import (
    SessionInformation,
    SessionInitializationBehavior,
)

_INITIALIZATION_BEHAVIOR = {
    SessionInitializationBehavior.AUTO: nifgen.SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: nifgen.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: nifgen.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: nifgen.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: nifgen.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
}


class SessionConstructor:
    """Constructs sessions based on SessionInformation."""

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        grpc_channel_pool: GrpcChannelPool,
        reset_device: bool,
        options: Optional[Dict[str, Any]],
        initialization_behavior: SessionInitializationBehavior,
    ) -> None:
        """Initialize the session constructor."""
        self._grpc_channel = get_insecure_grpc_device_channel(
            discovery_client, grpc_channel_pool, nifgen.GRPC_SERVICE_INTERFACE_NAME
        )
        self._reset_device = reset_device
        self._options = NIFGEN_OPTIONS.to_dict() if options is None else options
        self._initialization_behavior = _INITIALIZATION_BEHAVIOR[initialization_behavior]

    def __call__(self, session_info: SessionInformation) -> nifgen.Session:
        """Construct a session object."""
        kwargs: Dict[str, Any] = {}
        if self._grpc_channel:
            kwargs["grpc_options"] = nifgen.GrpcSessionOptions(
                grpc_channel=self._grpc_channel,
                session_name=session_info.session_name,
                initialization_behavior=self._initialization_behavior,
            )

        return nifgen.Session(
            resource_name=session_info.resource_name,
            reset_device=self._reset_device,
            options=self._options,
            **kwargs,
        )

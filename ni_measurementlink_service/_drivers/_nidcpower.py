from __future__ import annotations

from typing import Any, Dict, Optional

import nidcpower

from ni_measurementlink_service._configuration import NIDCPOWER_OPTIONS
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
    SessionInitializationBehavior.AUTO: nidcpower.SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: nidcpower.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: nidcpower.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: nidcpower.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: nidcpower.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
}


class SessionConstructor:
    """Constructs sessions based on SessionInformation."""

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        grpc_channel_pool: GrpcChannelPool,
        reset: bool,
        options: Optional[Dict[str, Any]],
        initialization_behavior: SessionInitializationBehavior,
    ) -> None:
        """Initialize the session constructor."""
        self._grpc_channel = get_insecure_grpc_device_server_channel(
            discovery_client, grpc_channel_pool, nidcpower.GRPC_SERVICE_INTERFACE_NAME
        )
        self._reset = reset
        self._options = NIDCPOWER_OPTIONS.to_dict() if options is None else options
        self._initialization_behavior = _INITIALIZATION_BEHAVIOR[initialization_behavior]

    def __call__(self, session_info: SessionInformation) -> nidcpower.Session:
        """Construct a session object."""
        kwargs: Dict[str, Any] = {}
        if self._grpc_channel:
            kwargs["grpc_options"] = nidcpower.GrpcSessionOptions(
                grpc_channel=self._grpc_channel,
                session_name=session_info.session_name,
                initialization_behavior=self._initialization_behavior,
            )

        return nidcpower.Session(
            resource_name=session_info.resource_name,
            reset=self._reset,
            options=self._options,
            **kwargs,
        )

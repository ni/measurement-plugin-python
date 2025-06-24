from __future__ import annotations

from typing import Any

import nidigital

from ni_measurement_plugin_sdk_service._configuration import NIDIGITAL_OPTIONS
from ni_measurement_plugin_sdk_service._drivers._grpcdevice import (
    get_insecure_grpc_device_server_channel,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.session_management._types import (
    SessionInformation,
    SessionInitializationBehavior,
)

_INITIALIZATION_BEHAVIOR = {
    SessionInitializationBehavior.AUTO: nidigital.SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: nidigital.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: nidigital.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: nidigital.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: nidigital.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
}


class SessionConstructor:
    """Constructs sessions based on SessionInformation."""

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        grpc_channel_pool: GrpcChannelPool,
        reset_device: bool,
        options: dict[str, Any] | None,
        initialization_behavior: SessionInitializationBehavior,
    ) -> None:
        """Initialize the session constructor."""
        self._grpc_channel = get_insecure_grpc_device_server_channel(
            discovery_client, grpc_channel_pool, nidigital.GRPC_SERVICE_INTERFACE_NAME
        )
        self._reset_device = reset_device
        self._options = NIDIGITAL_OPTIONS.to_dict() if options is None else options
        self._initialization_behavior = _INITIALIZATION_BEHAVIOR[initialization_behavior]

    def __call__(self, session_info: SessionInformation) -> nidigital.Session:
        """Construct a session object."""
        kwargs: dict[str, Any] = {}
        if self._grpc_channel:
            kwargs["grpc_options"] = nidigital.GrpcSessionOptions(
                grpc_channel=self._grpc_channel,
                session_name=session_info.session_name,
                initialization_behavior=self._initialization_behavior,
            )

        # Omit id_query because it has no effect.
        return nidigital.Session(
            resource_name=session_info.resource_name,
            reset_device=self._reset_device,
            options=self._options,
            **kwargs,
        )

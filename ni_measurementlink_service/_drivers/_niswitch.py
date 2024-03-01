from __future__ import annotations

from typing import Any, Dict, Optional, Union

import niswitch

from ni_measurementlink_service._configuration import NISWITCH_OPTIONS, NISWITCH_MULTIPLEXER_OPTIONS
from ni_measurementlink_service._drivers._grpcdevice import (
    get_insecure_grpc_device_server_channel,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool
from ni_measurementlink_service.session_management._types import (
    MultiplexerSessionInformation,
    SessionInformation,
    SessionInitializationBehavior,
)

_INITIALIZATION_BEHAVIOR = {
    SessionInitializationBehavior.AUTO: niswitch.SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: niswitch.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: niswitch.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
}


class SessionConstructor:
    """Constructs sessions based on SessionInformation."""

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        grpc_channel_pool: GrpcChannelPool,
        topology: Optional[str],
        simulate: Optional[bool],
        reset_device: bool,
        initialization_behavior: SessionInitializationBehavior,
        *,
        is_multiplexer: bool = False,
    ) -> None:
        """Initialize the session constructor."""
        self._grpc_channel = get_insecure_grpc_device_server_channel(
            discovery_client, grpc_channel_pool, niswitch.GRPC_SERVICE_INTERFACE_NAME
        )

        if is_multiplexer:
            self._topology = NISWITCH_MULTIPLEXER_OPTIONS.topology if topology is None else topology
            self._simulate = NISWITCH_MULTIPLEXER_OPTIONS.simulate if simulate is None else simulate
        else:
            self._topology = NISWITCH_OPTIONS.topology if topology is None else topology
            self._simulate = NISWITCH_OPTIONS.simulate if simulate is None else simulate

        self._reset_device = reset_device
        self._initialization_behavior = _INITIALIZATION_BEHAVIOR[initialization_behavior]

    def __call__(
        self, session_info: Union[SessionInformation, MultiplexerSessionInformation]
    ) -> niswitch.Session:
        """Construct a session object."""
        kwargs: Dict[str, Any] = {}
        if self._grpc_channel:
            kwargs["grpc_options"] = niswitch.GrpcSessionOptions(
                grpc_channel=self._grpc_channel,
                session_name=session_info.session_name,
                initialization_behavior=self._initialization_behavior,
            )

        # Initializing a nonexistent switch module returns
        # NISWITCH_ERROR_INVALID_RESOURCE_DESCRIPTOR, even if simulate=True.
        resource_name = "" if self._simulate else session_info.resource_name

        return niswitch.Session(
            resource_name=resource_name,
            topology=self._topology,
            simulate=self._simulate,
            reset_device=self._reset_device,
            **kwargs,
        )

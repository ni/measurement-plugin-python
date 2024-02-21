"""Functions to set up and tear down sessions of NI-SWITCH multiplexers in NI TestStand."""

from typing import Any

from _helpers import TestStandSupport
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.grpc.channelpool import GrpcChannelPool
from ni_measurementlink_service.session_management import (
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)


def create_niswitch_multiplexer_sessions(sequence_context: Any) -> None:
    """Create and register all NI-SWITCH multiplexer sessions.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPool() as grpc_channel_pool:
        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=None)

        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.get_multiplexer_sessions(pin_map_context) as session_handler:
            with session_handler.initialize_niswitch_multiplexer_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ):
                pass

            session_management_client.register_multiplexer_sessions(
                session_handler.multiplexer_session_info
            )


def destroy_niswitch_multiplexer_sessions() -> None:
    """Destroy and unregister all NI-SWITCH multiplexer sessions."""
    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.get_all_registered_multiplexer_sessions() as session_handler:
            if not session_handler.multiplexer_session_info:
                return

            session_management_client.unregister_multiplexer_sessions(
                session_handler.multiplexer_session_info
            )
            with session_handler.initialize_niswitch_multiplexer_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass

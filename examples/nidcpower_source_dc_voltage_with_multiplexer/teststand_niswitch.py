"""Functions to set up and tear down sessions of NI-Switch devices in NI TestStand."""

from typing import Any

from _helpers import TestStandSupport
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.session_management import (
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)


def create_niswitch_sessions(sequence_context: Any) -> None:
    """Create and register all NI-Switch sessions.

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
        with session_management_client.reserve_sessions(
            pin_map_context,
            instrument_type_id=INSTRUMENT_TYPE_NI_RELAY_DRIVER,
        ) as reservation:
            with reservation.initialize_niswitch_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ):
                pass

            session_management_client.register_sessions(reservation.session_info)


def destroy_niswitch_sessions() -> None:
    """Destroy and unregister all NI-Switch sessions."""
    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_NI_RELAY_DRIVER,
        ) as reservation:
            if not reservation.session_info:
                return

            session_management_client.unregister_sessions(reservation.session_info)

            with reservation.initialize_niswitch_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass


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
        with session_management_client.get_multiplexer_sessions(
            pin_map_context
        ) as session_container:
            with session_container.initialize_niswitch_multiplexer_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ):
                pass

            session_management_client.register_multiplexer_sessions(
                session_container.multiplexer_session_info
            )


def destroy_niswitch_multiplexer_sessions() -> None:
    """Destroy and unregister all NI-SWITCH multiplexer sessions."""
    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.get_all_registered_multiplexer_sessions() as session_container:
            if not session_container.multiplexer_session_info:
                return

            session_management_client.unregister_multiplexer_sessions(
                session_container.multiplexer_session_info
            )
            with session_container.initialize_niswitch_multiplexer_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass

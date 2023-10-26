"""Functions to set up and tear down sessions of NI-FGEN devices in NI TestStand."""
from typing import Any

from _helpers import GrpcChannelPoolHelper, TestStandSupport
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_FGEN,
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)


def create_nifgen_sessions(sequence_context: Any) -> None:
    """Create and register all NI-FGEN sessions.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=None)

        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_sessions(
            pin_map_context,
            instrument_type_id=INSTRUMENT_TYPE_NI_FGEN,
        ) as reservation:
            with reservation.initialize_nifgen_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ):
                pass

            session_management_client.register_sessions(reservation.session_info)


def destroy_nifgen_sessions() -> None:
    """Destroy and unregister all NI-FGEN sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_NI_FGEN,
        ) as reservation:
            if not reservation.session_info:
                return

            session_management_client.unregister_sessions(reservation.session_info)

            with reservation.initialize_nifgen_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass

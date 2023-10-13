"""Functions to set up and tear down sessions of NI-DCPower devices in NI TestStand."""
from typing import Any

import ni_measurementlink_service as nims
from _helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DCPOWER,
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)


def update_pin_map(pin_map_path: str, sequence_context: Any) -> str:
    """Update registered pin map contents.

    Create and register a pin map if a pin map resource for the specified pin map id is not found.

    Args:
        pin_map_path:
            An absolute or relative path to the pin map file.
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_abs_path = teststand_support.resolve_file_path(pin_map_path)

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        pin_map_client = PinMapClient(grpc_channel=grpc_channel_pool.pin_map_channel)
        pin_map_id = pin_map_client.update_pin_map(pin_map_abs_path)

    teststand_support.set_active_pin_map_id(pin_map_id)
    return pin_map_id


def create_nidcpower_sessions(sequence_context: Any) -> None:
    """Create and register all NI-DCPower sessions.

    Args:
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
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
            pin_map_context, instrument_type_id=INSTRUMENT_TYPE_NI_DCPOWER
        ) as reservation:
            # Initialize new sessions on the server, but do not close them.
            # (Deliberately leak them.)
            context_manager = reservation.create_nidcpower_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
            )
            _ = context_manager.__enter__()

            session_management_client.register_sessions(reservation.session_info)


def destroy_nidcpower_sessions() -> None:
    """Destroy and unregister all NI-DCPower sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_NI_DCPOWER
        ) as reservation:
            # If there are no registered sessions, there is nothing to clean up.
            if not reservation.session_info:
                return
            
            session_management_client.unregister_sessions(reservation.session_info)

            # Attach to the sessions on the server and explicitly close them.
            with reservation.create_nidcpower_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION
            ) as session_infos:
                for session_info in session_infos:
                    session_info.session.close()
                

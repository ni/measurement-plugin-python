"""Functions to set up and tear down sessions of NI-Switch devices in NI TestStand."""
from typing import Any

import ni_measurementlink_service as nims
import niswitch
from _helpers import GrpcChannelPoolHelper, TestStandSupport
from _niswitch_helpers import create_session


def create_niswitch_sessions(sequence_context: Any) -> None:
    """Create and register all NI-Switch sessions.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        grpc_device_channel = grpc_channel_pool.get_grpc_device_channel(
            niswitch.GRPC_SERVICE_INTERFACE_NAME
        )
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_RELAY_DRIVER,
        ) as reservation:
            for session_info in reservation.session_info:
                # Leave session open
                _ = create_session(
                    session_info,
                    grpc_device_channel,
                    initialization_behavior=niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

            session_management_client.register_sessions(reservation.session_info)


def destroy_niswitch_sessions() -> None:
    """Destroy and unregister all NI-Switch sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        grpc_device_channel = grpc_channel_pool.get_grpc_device_channel(
            niswitch.GRPC_SERVICE_INTERFACE_NAME
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_RELAY_DRIVER,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                session = create_session(
                    session_info,
                    grpc_device_channel,
                    initialization_behavior=niswitch.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session.close()

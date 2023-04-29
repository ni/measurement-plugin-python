"""TestStand code module for setting up NI-DMM sessions with MeasurementLink."""
from typing import Any

import nidmm
from _helpers import GrpcChannelPoolHelper, TestStandSupport

import ni_measurementlink_service as nims


def create_nidmm_sessions(sequence_context: Any) -> None:
    """Create and register all NI-DMM sessions.
        
    Args:
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DMM,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                grpc_options = nidmm.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(nidmm.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=nidmm.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

                # Leave session open
                nidmm.Session(resource_name=session_info.resource_name, grpc_options=grpc_options)

            session_management_client.register_sessions(reservation.session_info)


def destroy_nidmm_sessions() -> None:
    """Destroy and unregister all NI-DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DMM,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                grpc_options = nidmm.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(nidmm.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=nidmm.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session = nidmm.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )
                session.close()

"""Functions to set up and tear down sessions of NI-DCPower devices in NI TestStand."""
from typing import Any

import nidcpower
from nidcpower_source_dc_voltage._helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport

import ni_measurementlink_service as nims


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
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                grpc_options = nidcpower.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(
                        nidcpower.GRPC_SERVICE_INTERFACE_NAME
                    ),
                    session_name=session_info.session_name,
                    initialization_behavior=nidcpower.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

                # Leave session open
                nidcpower.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )

            session_management_client.register_sessions(reservation.session_info)


def destroy_nidcpower_sessions() -> None:
    """Destroy and unregister all NI-DCPower sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                grpc_options = nidcpower.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(
                        nidcpower.GRPC_SERVICE_INTERFACE_NAME
                    ),
                    session_name=session_info.session_name,
                    initialization_behavior=nidcpower.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session = nidcpower.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )
                session.close()

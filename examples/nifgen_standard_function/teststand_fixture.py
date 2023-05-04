"""Functions to set up and tear down sessions of NI-FGEN devices in NI TestStand."""
from typing import Any, Dict

import nifgen
from _helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport

import ni_measurementlink_service as nims

# To use a physical NI waveform generator instrument, set this to False.
USE_SIMULATION = True


def update_pin_map(pin_map_path: str, sequence_context: Any) -> None:
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


def create_nifgen_sessions(sequence_context: Any) -> None:
    """Create and register all NI-FGEN sessions.

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
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                options: Dict[str, Any] = {}
                if USE_SIMULATION:
                    options["simulate"] = True
                    options["driver_setup"] = {"Model": "5423 (2CH)"}

                grpc_options = nifgen.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(nifgen.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=nifgen.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

                # Leave session open
                nifgen.Session(
                    resource_name=session_info.resource_name,
                    channel_name=session_info.channel_list,
                    options=options,
                    grpc_options=grpc_options,
                )

            session_management_client.register_sessions(reservation.session_info)


def destroy_nifgen_sessions() -> None:
    """Destroy and unregister all NI-FGEN sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_FGEN,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                grpc_options = nifgen.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(nifgen.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=nifgen.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session = nifgen.Session(
                    resource_name=session_info.resource_name,
                    channel_name=session_info.channel_list,
                    grpc_options=grpc_options,
                )
                session.close()

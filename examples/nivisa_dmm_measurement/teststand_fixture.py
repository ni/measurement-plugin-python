"""Functions to set up and tear down NI-VISA DMM sessions in NI TestStand."""

import pyvisa.resources
from _helpers import GrpcChannelPoolHelper, PinMapClient
from _visa_helpers import (
    INSTRUMENT_TYPE_DMM_SIMULATOR,
    create_visa_resource_manager,
    create_visa_session,
    log_instrument_id,
    reset_instrument,
)

import ni_measurementlink_service as nims

# To use NI Instrument Simulator v2.0 hardware, set this to False.
USE_SIMULATION = True


def update_pin_map(pin_map_id: str) -> None:
    """Update registered pin map contents.

    Create and register a pin map if a pin map resource for the specified pin map id is not found.

    Args:
        pin_map_id (str): The resource id of the pin map to register as a pin map resource. By
            convention, the pin_map_id is the .pinmap file path.

    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        pin_map_client = PinMapClient(grpc_channel=grpc_channel_pool.pin_map_channel)
        pin_map_client.update_pin_map(pin_map_id)


def create_nivisa_dmm_sessions(pin_map_id: str) -> None:
    """Create and register all NI-VISA DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            resource_manager = create_visa_resource_manager(USE_SIMULATION)

            for session_info in reservation.session_info:
                with create_visa_session(resource_manager, session_info.resource_name) as session:
                    # Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation
                    # for Resource context manager implicitly upcasts derived class to base class
                    assert isinstance(session, pyvisa.resources.MessageBasedResource)
                    log_instrument_id(session)
                    reset_instrument(session)

            session_management_client.register_sessions(reservation.session_info)


def destroy_nivisa_dmm_sessions() -> None:
    """Destroy and unregister all NI-VISA DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

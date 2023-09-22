"""Functions to set up and tear down NI-VISA DMM sessions in NI TestStand."""
from typing import Any

import pyvisa.resources
from _constants import USE_SIMULATION
from _helpers import GrpcChannelPoolHelper, TestStandSupport
from _visa_helpers import (
    INSTRUMENT_TYPE_DMM_SIMULATOR,
    create_resource_manager,
    create_session,
    log_instrument_id,
    reset_instrument,
)

import ni_measurementlink_service as nims


def create_nivisa_dmm_sessions(sequence_context: Any) -> None:
    """Create and register all NI-VISA DMM sessions.

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
            context=pin_map_context, instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR
        ) as reservation:
            resource_manager = create_resource_manager(USE_SIMULATION)

            for session_info in reservation.session_info:
                with create_session(session_info.resource_name, resource_manager) as session:
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
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

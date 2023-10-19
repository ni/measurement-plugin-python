"""Functions to set up and tear down NI-VISA DMM sessions in NI TestStand."""
from typing import Any

import ni_measurementlink_service as nims
from _constants import USE_SIMULATION
from _helpers import GrpcChannelPoolHelper, TestStandSupport
from _visa_dmm import INSTRUMENT_TYPE_VISA_DMM, Session


def create_nivisa_dmm_sessions(sequence_context: Any) -> None:
    """Create and register all NI-VISA DMM sessions.

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
        with session_management_client.reserve_sessions(
            context=pin_map_context, instrument_type_id=INSTRUMENT_TYPE_VISA_DMM
        ) as reservation:
            for session_info in reservation.session_info:
                # Reset the device
                with Session(
                    session_info.resource_name,
                    simulate=USE_SIMULATION,
                    reset_device=True,
                ) as _:
                    pass

            session_management_client.register_sessions(reservation.session_info)


def destroy_nivisa_dmm_sessions() -> None:
    """Destroy and unregister all NI-VISA DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_VISA_DMM,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

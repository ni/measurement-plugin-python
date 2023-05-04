"""Functions to set up and tear down python-ivi DMM sessions in NI TestStand."""
import contextlib
import sys
from typing import Any

import pyvisa
from _helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport

import ni_measurementlink_service as nims

try:
    # HACK: python-ivi expects to be able to import pyvisa using "import visa" as of the last
    # commit on 2/18/2017.
    sys.modules["visa"] = pyvisa
    import ivi
finally:
    pass

# To use a physical instrument, set this to False.
USE_SIMULATION = True

INSTRUMENT_TYPE_AG34401A = "ag34401A"


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


def create_python_ivi_dmm_sessions(sequence_context: Any) -> None:
    """Create and register all python-ivi DMM sessions.

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
            instrument_type_id=INSTRUMENT_TYPE_AG34401A,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                with contextlib.closing(
                    ivi.agilent.agilent34401A(
                        session_info.resource_name, reset=True, simulate=USE_SIMULATION
                    )
                ) as session:
                    # HACK: python-ivi doesn't close pyvisa sessions as of the last commit on
                    # 2/18/2017.
                    if (
                        session is not None
                        and session._interface is not None
                        and session._interface.instrument is not None
                    ):
                        session._interface.instrument.close()

            session_management_client.register_sessions(reservation.session_info)


def destroy_python_ivi_dmm_sessions() -> None:
    """Destroy and unregister all python-ivi DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_AG34401A,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

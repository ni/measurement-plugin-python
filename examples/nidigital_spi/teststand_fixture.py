"""Functions to set up and tear down sessions of NI Digital Pattern instruments in NI TestStand."""
from typing import Any, Iterable

import nidigital
from _helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport
from _nidigital_helpers import create_session

import ni_measurementlink_service as nims
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
)

# To use a physical NI Digital Pattern instrument, set this to False.
USE_SIMULATION = True


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


def create_nidigital_sessions(sequence_context: Any) -> None:
    """Create and register all NI-Digital sessions.

    Args:
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            for session_info in reservation.session_info:
                # Leave session open.
                _ = _create_new_nidigital_session(grpc_channel_pool, session_info)

            session_management_client.register_sessions(reservation.session_info)


def load_nidigital_pin_map(pin_map_path: str, sequence_context: Any) -> None:
    """Load the pin map into the registered NI-Digital sessions.

    Args:
        pin_map_path:
            An absolute or relative path to the pin map file.
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    pin_map_abs_path = teststand_support.resolve_file_path(pin_map_path)

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            for session_info in reservation.session_info:
                with _attach_nidigital_session(grpc_channel_pool, session_info) as session:
                    session.load_pin_map(pin_map_abs_path)


def load_nidigital_specifications_levels_and_timing(
    specifications_file_paths: Iterable[str],
    levels_file_paths: Iterable[str],
    timing_file_paths: Iterable[str],
    sequence_context: Any,
) -> None:
    """Load specifications, levels, and timing files into NI-Digital sessions.

    Args:
        specifications_file_paths:
            Absolute or relative paths to the specifications files.
        levels_file_paths:
            Absolute or relative paths to the levels files.
        timing_file_paths:
            Absolute or relative paths to the timing files.
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    specifications_file_abs_paths = [
        teststand_support.resolve_file_path(p) for p in specifications_file_paths
    ]
    levels_file_abs_paths = [teststand_support.resolve_file_path(p) for p in levels_file_paths]
    timing_file_abs_paths = [teststand_support.resolve_file_path(p) for p in timing_file_paths]

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            for session_info in reservation.session_info:
                with _attach_nidigital_session(grpc_channel_pool, session_info) as session:
                    session.load_specifications_levels_and_timing(
                        specifications_file_abs_paths, levels_file_abs_paths, timing_file_abs_paths
                    )


def load_nidigital_patterns(
    pattern_file_paths: Iterable[str],
    sequence_context: Any,
) -> None:
    """Load specifications, levels, and timing files into NI-Digital sessions.

    Args:
        pattern_file_paths:
            Absolute or relative paths to the pattern files.
        sequence_context:
            The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    pattern_file_abs_paths = [teststand_support.resolve_file_path(p) for p in pattern_file_paths]

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            for session_info in reservation.session_info:
                with _attach_nidigital_session(grpc_channel_pool, session_info) as session:
                    for pattern_file_abs_path in pattern_file_abs_paths:
                        session.load_pattern(pattern_file_abs_path)


def destroy_nidigital_sessions() -> None:
    """Destroy and unregister all NI-Digital sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                session = _attach_nidigital_session(grpc_channel_pool, session_info)
                session.close()


def _reserve_sessions(
    session_management_client: nims.session_management.Client,
    pin_map_id: str,
    instrument_type_id: str,
) -> nims.session_management.MultiSessionReservation:
    pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)

    return session_management_client.reserve_sessions(
        context=pin_map_context,
        instrument_type_id=instrument_type_id,
        # This code module sets up the sessions, so error immediately if they are in use.
        timeout=0,
    )


def _create_new_nidigital_session(
    grpc_channel_pool: GrpcChannelPoolHelper,
    session_info: nims.session_management.SessionInformation,
) -> nidigital.Session:
    grpc_device_channel = grpc_channel_pool.get_grpc_device_channel(
        nidigital.GRPC_SERVICE_INTERFACE_NAME
    )
    return create_session(
        session_info,
        grpc_device_channel,
        initialization_behavior=nidigital.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    )


def _attach_nidigital_session(
    grpc_channel_pool: GrpcChannelPoolHelper,
    session_info: nims.session_management.SessionInformation,
) -> nidigital.Session:
    grpc_device_channel = grpc_channel_pool.get_grpc_device_channel(
        nidigital.GRPC_SERVICE_INTERFACE_NAME
    )
    return create_session(
        session_info,
        grpc_device_channel,
        initialization_behavior=nidigital.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    )

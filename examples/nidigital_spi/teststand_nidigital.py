"""Functions to set up and tear down sessions of NI Digital Pattern instruments in NI TestStand."""

from collections.abc import Iterable
from typing import Any

from _helpers import TestStandSupport
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.session_management import (
    INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)
from ni_measurement_plugin_sdk_service.session_management._reservation import (
    MultiSessionReservation,
)


def create_nidigital_sessions(sequence_context: Any) -> None:
    """Create and register all NI-Digital sessions.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()

    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            with reservation.initialize_nidigital_sessions(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ):
                pass

            session_management_client.register_sessions(reservation.session_info)


def load_nidigital_pin_map(pin_map_path: str, sequence_context: Any) -> None:
    """Load the pin map into the registered NI-Digital sessions.

    Args:
        pin_map_path: An absolute or relative path to the pin map file.
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    pin_map_abs_path = teststand_support.resolve_file_path(pin_map_path)

    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            with reservation.initialize_nidigital_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION
            ) as session_infos:
                for session_info in session_infos:
                    session_info.session.load_pin_map(pin_map_abs_path)


def load_nidigital_specifications_levels_and_timing(
    specifications_file_paths: Iterable[str],
    levels_file_paths: Iterable[str],
    timing_file_paths: Iterable[str],
    sequence_context: Any,
) -> None:
    """Load specifications, levels, and timing files into NI-Digital sessions.

    Args:
        specifications_file_paths: Absolute or relative paths to the specifications files.
        levels_file_paths: Absolute or relative paths to the levels files.
        timing_file_paths: Absolute or relative paths to the timing files.
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    specifications_file_abs_paths = [
        teststand_support.resolve_file_path(p) for p in specifications_file_paths
    ]
    levels_file_abs_paths = [teststand_support.resolve_file_path(p) for p in levels_file_paths]
    timing_file_abs_paths = [teststand_support.resolve_file_path(p) for p in timing_file_paths]

    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            with reservation.initialize_nidigital_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION
            ) as session_infos:
                for session_info in session_infos:
                    session_info.session.load_specifications_levels_and_timing(
                        specifications_file_abs_paths, levels_file_abs_paths, timing_file_abs_paths
                    )


def load_nidigital_patterns(
    pattern_file_paths: Iterable[str],
    sequence_context: Any,
) -> None:
    """Load specifications, levels, and timing files into NI-Digital sessions.

    Args:
        pattern_file_paths: Absolute or relative paths to the pattern files.
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_id = teststand_support.get_active_pin_map_id()
    pattern_file_abs_paths = [teststand_support.resolve_file_path(p) for p in pattern_file_paths]

    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with _reserve_sessions(
            session_management_client, pin_map_id, INSTRUMENT_TYPE_NI_DIGITAL_PATTERN
        ) as reservation:
            with reservation.initialize_nidigital_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION
            ) as session_infos:
                for session_info in session_infos:
                    for pattern_file_abs_path in pattern_file_abs_paths:
                        session_info.session.load_pattern(pattern_file_abs_path)


def destroy_nidigital_sessions() -> None:
    """Destroy and unregister all NI-Digital sessions."""
    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
        ) as reservation:
            if not reservation.session_info:
                return

            session_management_client.unregister_sessions(reservation.session_info)
            with reservation.initialize_nidigital_sessions(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass


def _reserve_sessions(
    session_management_client: SessionManagementClient,
    pin_map_id: str,
    instrument_type_id: str,
) -> MultiSessionReservation:
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=None)

    return session_management_client.reserve_sessions(
        pin_map_context, instrument_type_id=instrument_type_id
    )

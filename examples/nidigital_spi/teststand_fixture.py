"""Functions to set up and tear down sessions of NI Digital Pattern instruments in NI TestStand."""
import pathlib
from typing import Iterable, Union

import nidigital
from _helpers import GrpcChannelPoolHelper, PinMapClient

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent


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


def create_nidigital_sessions(
    pin_map_id: str,
    specifications_file_paths: Iterable[str],
    levels_file_paths: Iterable[str],
    timing_file_paths: Iterable[str],
    pattern_file_paths: Iterable[str],
) -> None:
    """Create and register all NI-Digital sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                grpc_options = nidigital.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(
                        nidigital.GRPC_SERVICE_INTERFACE_NAME
                    ),
                    session_name=session_info.session_name,
                    initialization_behavior=nidigital.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

                session = nidigital.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )
                # Preload the pin map, specifications, levels, timing, and pattern files.
                session.load_pin_map(pin_map_id)
                session.load_specifications_levels_and_timing(
                    [
                        str(_resolve_relative_path(service_directory, path))
                        for path in specifications_file_paths
                    ],
                    [
                        str(_resolve_relative_path(service_directory, path))
                        for path in levels_file_paths
                    ],
                    [
                        str(_resolve_relative_path(service_directory, path))
                        for path in timing_file_paths
                    ],
                )
                for path in pattern_file_paths:
                    session.load_pattern(str(_resolve_relative_path(service_directory, path)))
                # Leave session open

            session_management_client.register_sessions(reservation.session_info)


def _resolve_relative_path(
    directory_path: pathlib.Path, file_path: Union[str, pathlib.Path]
) -> pathlib.Path:
    if not isinstance(file_path, pathlib.Path):
        file_path = pathlib.Path(file_path)
    if file_path.is_absolute():
        return file_path
    else:
        return (directory_path / file_path).resolve()


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
                grpc_options = nidigital.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(
                        nidigital.GRPC_SERVICE_INTERFACE_NAME
                    ),
                    session_name=session_info.session_name,
                    initialization_behavior=nidigital.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session = nidigital.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )
                session.close()

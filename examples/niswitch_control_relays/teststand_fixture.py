"""Functions to set up and tear down sessions of NI-Switch devices in NI TestStand."""

import niswitch
from _helpers import GrpcChannelPoolHelper, PinMapClient

import ni_measurementlink_service as nims

# To use a physical NI relay driver instrument, set this to False.
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


def create_niswitch_sessions(pin_map_id: str) -> None:
    """Create and register all NI-Switch sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_RELAY_DRIVER,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            for session_info in reservation.session_info:
                options = {}
                if service_options.use_simulation:
                    options["simulate"] = True
                    options["driver_setup"] = {"Model": "2567"}

                grpc_options = niswitch.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(niswitch.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=niswitch.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
                )

                # Leave session open
                niswitch.Session(
                    resource_name=session_info.resource_name,
                    options=options,
                    grpc_options=grpc_options,
                )

            session_management_client.register_sessions(reservation.session_info)


def destroy_niswitch_sessions() -> None:
    """Destroy and unregister all NI-Switch sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_RELAY_DRIVER,
            # This code module sets up the sessions, so error immediately if they are in use.
            timeout=0,
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            for session_info in reservation.session_info:
                grpc_options = niswitch.GrpcSessionOptions(
                    grpc_channel_pool.get_grpc_device_channel(niswitch.GRPC_SERVICE_INTERFACE_NAME),
                    session_name=session_info.session_name,
                    initialization_behavior=niswitch.SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
                )

                session = niswitch.Session(
                    resource_name=session_info.resource_name, grpc_options=grpc_options
                )
                session.close()

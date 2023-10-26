"""Functions to set up and tear down sessions of NI-DAQmx devices in NI TestStand."""
from typing import Any

from _helpers import GrpcChannelPoolHelper, TestStandSupport
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DAQMX,
    PinMapContext,
    SessionInitializationBehavior,
    SessionManagementClient,
)


def create_nidaqmx_tasks(sequence_context: Any) -> None:
    """Create and register all NI-DAQmx tasks.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=None)

        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )

        with session_management_client.reserve_sessions(
            pin_map_context, instrument_type_id=INSTRUMENT_TYPE_NI_DAQMX
        ) as reservation:
            with reservation.create_nidaqmx_tasks(
                initialization_behavior=SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH
            ) as tasks:
                for task in tasks:
                    task.session.ai_channels.add_ai_voltage_chan(task.channel_list)

            session_management_client.register_sessions(reservation.session_info)


def destroy_nidaqmx_tasks() -> None:
    """Destroy and unregister all NI-DAQmx tasks."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_NI_DAQMX,
        ) as reservation:
            if not reservation.session_info:
                return

            session_management_client.unregister_sessions(reservation.session_info)
            with reservation.create_nidaqmx_tasks(
                initialization_behavior=SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE
            ):
                pass

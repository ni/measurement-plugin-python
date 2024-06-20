"""Functions to set up and tear down NI-VISA DMM sessions in NI TestStand."""

import pathlib
from typing import Any

from _helpers import TestStandSupport
from _visa_dmm import INSTRUMENT_TYPE_VISA_DMM
from _visa_dmm_session_management import VisaDmmSessionConstructor
from decouple import AutoConfig
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.session_management import (
    PinMapContext,
    SessionManagementClient,
)
from ni_measurement_plugin_sdk_service.session_management._types import (
    SessionInitializationBehavior,
)

# Search for the `.env` file starting with this code module's parent directory.
_config = AutoConfig(str(pathlib.Path(__file__).resolve().parent))
_VISA_DMM_SIMULATE: bool = _config("MEASUREMENT_PLUGIN_VISA_DMM_SIMULATE", default=False, cast=bool)


def create_nivisa_dmm_sessions(sequence_context: Any) -> None:
    """Create and register all NI-VISA DMM sessions.

    Args:
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    with GrpcChannelPool() as grpc_channel_pool:
        teststand_support = TestStandSupport(sequence_context)
        pin_map_id = teststand_support.get_active_pin_map_id()
        pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=None)

        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        session_constructor = VisaDmmSessionConstructor(
            _config,
            discovery_client,
            SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH,
        )

        with session_management_client.reserve_sessions(
            context=pin_map_context, instrument_type_id=INSTRUMENT_TYPE_VISA_DMM
        ) as reservation:
            with reservation.initialize_sessions(
                session_constructor, instrument_type_id=INSTRUMENT_TYPE_VISA_DMM
            ):
                pass

            session_management_client.register_sessions(reservation.session_info)


def destroy_nivisa_dmm_sessions() -> None:
    """Destroy and unregister all NI-VISA DMM sessions."""
    with GrpcChannelPool() as grpc_channel_pool:
        discovery_client = DiscoveryClient(grpc_channel_pool=grpc_channel_pool)
        session_management_client = SessionManagementClient(
            discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
        )
        session_constructor = VisaDmmSessionConstructor(
            _config,
            discovery_client,
            SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE,
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_VISA_DMM,
        ) as reservation:
            if not reservation.session_info:
                return

            with reservation.initialize_sessions(
                session_constructor, instrument_type_id=INSTRUMENT_TYPE_VISA_DMM
            ):
                pass

            session_management_client.unregister_sessions(reservation.session_info)

"""Functions to set up and tear down NI-VISA DMM sessions in NI TestStand."""

import logging
import pathlib

import pyvisa
import pyvisa.resources
import pyvisa.typing
from _helpers import GrpcChannelPoolHelper, PinMapClient

import ni_measurementlink_service as nims


INSTRUMENT_TYPE_DMM_SIMULATOR = "DigitalMultimeterSimulator"
SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "NIInstrumentSimulatorV2_0.yaml"

# If you don't have NI Instrument Simulator v2.0 hardware, you can simulate it in software by
# setting this constant to True and running measurement.py --use-simulation.
USE_SIMULATION = False


def update_pin_map(pin_map_id: str):
    """Update registered pin map contents.

    Create and register a pin map if a pin map resource for the specified pin map id is not found.

    Args:
    ----
        pin_map_id (str): The resource id of the pin map to register as a pin map resource. By
            convention, the pin_map_id is the .pinmap file path.

    """
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        pin_map_client = PinMapClient(grpc_channel=grpc_channel_pool.pin_map_channel)
        pin_map_client.update_pin_map(pin_map_id)


def create_nivisa_dmm_sessions(pin_map_id: str):
    """Create and register all NI-VISA DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        pin_map_context = nims.session_management.PinMapContext(pin_map_id=pin_map_id, sites=None)
        with session_management_client.reserve_sessions(
            context=pin_map_context,
            instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
            timeout=-1,
        ) as reservation:
            resource_manager = pyvisa.ResourceManager(
                f"{SIMULATION_YAML_PATH}@sim" if USE_SIMULATION else ""
            )

            for session_info in reservation.session_info:
                with _create_visa_session(resource_manager, session_info.resource_name) as session:
                    instrument_id = session.query("*IDN?")
                    logging.info("Instrument: %s", instrument_id)

                    session.write("*RST")

            session_management_client.register_sessions(reservation.session_info)


def destroy_nivisa_dmm_sessions():
    """Destroy and unregister all NI-VISA DMM sessions."""
    with GrpcChannelPoolHelper() as grpc_channel_pool:
        session_management_client = nims.session_management.Client(
            grpc_channel=grpc_channel_pool.session_management_channel
        )

        with session_management_client.reserve_all_registered_sessions(
            instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR, timeout=-1
        ) as reservation:
            session_management_client.unregister_sessions(reservation.session_info)

            resource_manager = pyvisa.ResourceManager(
                f"{SIMULATION_YAML_PATH}@sim" if USE_SIMULATION else ""
            )

            for session_info in reservation.session_info:
                with _create_visa_session(resource_manager, session_info.resource_name) as session:
                    session.write("*RST")


def _create_visa_session(
    resource_manager: pyvisa.ResourceManager, resource_name: str
) -> pyvisa.resources.MessageBasedResource:
    session = resource_manager.open_resource(resource_name)
    assert isinstance(session, pyvisa.resources.MessageBasedResource)
    # The NI Instrument Simulator hardware accepts either \r\n or \n but the simulation YAML needs
    # the newlines to match.
    session.read_termination = "\n"
    session.write_termination = "\n"
    return session

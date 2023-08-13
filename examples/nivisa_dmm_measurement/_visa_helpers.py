"""Helper classes and functions for MeasurementLink NI-VISA examples."""

import logging
import pathlib

import pyvisa
import pyvisa.resources
import pyvisa.typing

# Pin map instrument type constants for NI Instrument Simulator v2.0
INSTRUMENT_TYPE_FGEN_SIMULATOR = "WaveformGeneratorSimulator"
INSTRUMENT_TYPE_SCOPE_SIMULATOR = "OscilloscopeSimulator"
INSTRUMENT_TYPE_DMM_SIMULATOR = "DigitalMultimeterSimulator"

SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "NIInstrumentSimulatorV2_0.yaml"
"""
Path to a simulation YAML file that can be used to simulate an NI Instrument Simulator v2.0
with pyvisa-sim
"""


def create_visa_resource_manager(
    use_simulation: bool, simulation_yaml_path: pathlib.Path = SIMULATION_YAML_PATH
) -> pyvisa.ResourceManager:
    """Create a real or simulated VISA resource manager."""
    visa_library = f"{simulation_yaml_path}@sim" if use_simulation else ""
    return pyvisa.ResourceManager(visa_library)


def create_visa_session(
    resource_manager: pyvisa.ResourceManager, resource_name: str
) -> pyvisa.resources.MessageBasedResource:
    """Create a VISA session."""
    # The NI Instrument Simulator hardware accepts either \r\n or \n but the simulation YAML needs
    # the newlines to match.
    session = resource_manager.open_resource(
        resource_name, read_termination="\n", write_termination="\n"
    )
    assert isinstance(session, pyvisa.resources.MessageBasedResource)
    return session


def check_instrument_error(session: pyvisa.resources.MessageBasedResource) -> None:
    """Query the instrument's error queue."""
    response = session.query("SYST:ERR?")
    fields = response.split(",", maxsplit=1)
    assert len(fields) >= 1
    if int(fields[0]) != 0:
        raise RuntimeError("Instrument returned error %s: %s" % (fields[0], fields[1]))


def log_instrument_id(session: pyvisa.resources.MessageBasedResource) -> None:
    """Log the instrument's identification string."""
    instrument_id = session.query("*IDN?")
    logging.info("Instrument: %s", instrument_id)


def reset_instrument(session: pyvisa.resources.MessageBasedResource) -> None:
    """Reset the instrument to a known state."""
    session.write("*CLS")
    session.write("*RST")
    check_instrument_error(session)

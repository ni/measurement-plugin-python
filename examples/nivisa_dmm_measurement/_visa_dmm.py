"""Helper classes and functions for MeasurementLink NI-VISA examples."""

import logging
import pathlib
import sys
from enum import Enum
from types import TracebackType
from typing import (
    Optional,
    Type,
)

import pyvisa
import pyvisa.resources
import pyvisa.typing


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


# Pin map instrument type constants for NI Instrument Simulator v2.0
INSTRUMENT_TYPE_DMM_SIMULATOR = "DigitalMultimeterSimulator"

SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "_visa_dmm_sim.yaml"
"""
Path to a simulation YAML file that can be used to simulate an NI Instrument Simulator v2.0
with pyvisa-sim.
"""

RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}


class Function(Enum):
    """Function that represents the measurement type."""

    DC_VOLTS = 0
    AC_VOLTS = 1


FUNCTION_TO_VALUE = {
    Function.DC_VOLTS: "VOLT:DC",
    Function.AC_VOLTS: "VOLT:AC",
}


class Session:
    """An NI-VISA DMM session."""

    def __init__(
        self,
        resource_name: str,
        id_query: bool = True,
        reset_device: bool = True,
        use_simulation: bool = False,
    ) -> None:
        """Create a real or simulated VISA resource manager."""
        visa_library = f"{SIMULATION_YAML_PATH}@sim" if use_simulation else ""
        self._resource_manager = pyvisa.ResourceManager(visa_library)

        """Create session"""
        self._session = self._resource_manager.open_resource(
            resource_name, read_termination="\n", write_termination="\n"
        )

        """Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation for Resource
        # context manager implicitly upcasts derived class to base class"""
        assert isinstance(self._session, pyvisa.resources.MessageBasedResource)

        """Log the instrument's identification string."""
        if id_query:
            _log_instrument_id(self._session)

        """Reset the instrument"""
        if reset_device:
            _reset_instrument(self._session)

    def _close(self: Self) -> None:
        self._session.close()

    def __enter__(self: Self) -> Self:
        """Context management protocol. Returns self."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Context management protocol. Calls _close()."""
        self._close()

    def configure_measurement_digits(
        self, measurement_type: Function, range: float, resolution_digits: float
    ) -> None:
        """Configures the common properties of the measurement.

        These properties include method, range, and resolution_digits.
        """
        function_enum = FUNCTION_TO_VALUE[measurement_type]
        resolution_value = RESOLUTION_DIGITS_TO_VALUE[str(resolution_digits)]

        """Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation for Resource
        # context manager implicitly upcasts derived class to base class"""
        assert isinstance(self._session, pyvisa.resources.MessageBasedResource)

        self._session.write(
            "CONF:%s %.g,%.g" % (function_enum, range, resolution_value)
        )
        _check_instrument_error(self._session)

    def read(self) -> float:
        """Acquires a single measurement and returns the measured value."""
        assert isinstance(self._session, pyvisa.resources.MessageBasedResource)

        response = self._session.query("READ?")
        _check_instrument_error(self._session)
        return float(response)


def _check_instrument_error(session: pyvisa.resources.MessageBasedResource) -> None:
    """Query the instrument's error queue."""
    response = session.query("SYST:ERR?")
    fields = response.split(",", maxsplit=1)
    assert len(fields) >= 1
    if int(fields[0]) != 0:
        raise RuntimeError("Instrument returned error %s: %s" % (fields[0], fields[1]))


def _log_instrument_id(session: pyvisa.resources.MessageBasedResource) -> None:
    """Log the instrument's identification string."""
    instrument_id = session.query("*IDN?")
    logging.info("Instrument: %s", instrument_id)


def _reset_instrument(session: pyvisa.resources.MessageBasedResource) -> None:
    """Reset the instrument to a known state."""
    session.write("*CLS")
    session.write("*RST")
    _check_instrument_error(session)

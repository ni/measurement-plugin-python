"""Custom instrument driver for measurement plug-in NI-VISA DMM examples."""

from __future__ import annotations

import pathlib
import sys
from enum import Enum
from types import TracebackType
from typing import TYPE_CHECKING

import pyvisa
import pyvisa.resources
import pyvisa.typing

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


# Pin map instrument type constant for VISA DMM
INSTRUMENT_TYPE_VISA_DMM = "VisaDmm"

_SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "_visa_dmm_sim.yaml"

_RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}

# Supported NI-VISA DMM instrument IDs, both real and simulated, can be added here
_SUPPORTED_INSTRUMENT_IDS = [
    # Keysight/Agilent/HP 34401A
    "34401",
    "34410",
    "34411",
    "L4411",
    # NI Instrument Simulator v2.0
    "Instrument Simulator",  # single instrument
    "Waveform Generator Simulator",  # multi-instrument
]


class Function(Enum):
    """Enum that represents the measurement function."""

    DC_VOLTS = 0
    AC_VOLTS = 1


_FUNCTION_TO_VALUE = {
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
        simulate: bool = False,
    ) -> None:
        """Open NI-VISA DMM session."""
        # Create a real or simulated VISA resource manager."""
        visa_library = f"{_SIMULATION_YAML_PATH}@sim" if simulate else ""
        resource_manager = pyvisa.ResourceManager(visa_library)

        session = resource_manager.open_resource(
            resource_name, read_termination="\n", write_termination="\n"
        )

        if not isinstance(session, pyvisa.resources.MessageBasedResource):
            raise TypeError("The 'session' object must be an instance of MessageBasedResource.")
        self._session = session

        if id_query:
            self._validate_id()

        if reset_device:
            self._reset()

    def close(self) -> None:
        """Close the session."""
        self._session.close()

    def __enter__(self) -> Self:
        """Context management protocol. Returns self."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Context management protocol. Calls close()."""
        self.close()

    def configure_measurement_digits(
        self, function: Function, range: float, resolution_digits: float
    ) -> None:
        """Configure the common properties of the measurement.

        These properties include function, range, and resolution_digits.
        """
        function_enum = _FUNCTION_TO_VALUE[function]
        resolution_value = _RESOLUTION_DIGITS_TO_VALUE[str(resolution_digits)]

        self._session.write("CONF:%s %.g,%.g" % (function_enum, range, resolution_value))
        self._check_error()

    def read(self) -> float:
        """Acquires a single measurement and returns the measured value."""
        response = self._session.query("READ?")
        self._check_error()
        return float(response)

    def _check_error(self) -> None:
        """Query the instrument's error queue."""
        response = self._session.query("SYST:ERR?")
        fields = response.split(",", maxsplit=1)
        assert len(fields) >= 1
        if int(fields[0]) != 0:
            raise RuntimeError("Instrument returned error %s: %s" % (fields[0], fields[1]))

    def _validate_id(self) -> None:
        """Check the selected instrument is proper and responding.."""
        instrument_id = self._session.query("*IDN?")
        if not any(id_check in instrument_id for id_check in _SUPPORTED_INSTRUMENT_IDS):
            raise RuntimeError(
                "The ID query failed. This may mean that you selected the wrong instrument, your instrument did not respond, "
                f"or you are using a model that is not officially supported by this driver. Instrument ID: {instrument_id}"
            )

    def _reset(self) -> None:
        """Reset the instrument to a known state."""
        self._session.write("*CLS")
        self._session.write("*RST")
        self._check_error()

"""Custom instrument driver for MeasurementLink NI-VISA DMM examples."""
from __future__ import annotations

import pathlib
import sys
from enum import Enum
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Optional,
    Type,
)

import pyvisa
import pyvisa.resources
import pyvisa.typing


if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


# Pin map instrument type constants for VISA DMM Simulator
INSTRUMENT_TYPE_VISA_DMM = "VisaDmm"

_SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "_visa_dmm_sim.yaml"

_RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}

# Supported NI-VISA DMM instrument IDs, both real and simulated, can be added here
_VALID_INSTRUMENT_ID = [INSTRUMENT_TYPE_VISA_DMM, "34401"]


class Function(Enum):
    """Enum that represents the measurement function."""

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
        """Open Ni-VISA DMM session."""
        # Create a real or simulated VISA resource manager."""
        visa_library = f"{_SIMULATION_YAML_PATH}@sim" if use_simulation else ""
        resource_manager = pyvisa.ResourceManager(visa_library)

        session = resource_manager.open_resource(
            resource_name, read_termination="\n", write_termination="\n"
        )
        # Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation for Resource
        # context manager implicitly upcasts derived class to base class
        assert isinstance(session, pyvisa.resources.MessageBasedResource)
        self._session: pyvisa.resources.MessageBasedResource = session

        if id_query:
            self._validate()

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
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Context management protocol. Calls _close()."""
        self.close()

    def configure_measurement_digits(
        self, measurement_type: Function, range: float, resolution_digits: float
    ) -> None:
        """Configures the common properties of the measurement.

        These properties include function, range, and resolution_digits.
        """
        function_enum = FUNCTION_TO_VALUE[measurement_type]
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

    def _validate(self) -> None:
        """Check the selected instrument is proper and responding.."""
        instrument_id = self._session.query("*IDN?")
        if not any(id_check in instrument_id for id_check in _VALID_INSTRUMENT_ID):
            raise RuntimeError(
                "The Instrument is not responding properly and the returned instrument_id is %s"
                % (instrument_id)
            )

    def _reset(self) -> None:
        """Reset the instrument to a known state."""
        self._session.write("*CLS")
        self._session.write("*RST")
        self._check_error()

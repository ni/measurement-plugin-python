
from enum import Enum
import pathlib

import grpc
import pyvisa
import pyvisa.resources
import pyvisa.typing

from driver_pb2 import InitializeRequest, InitializeResponse, ConfigureMeasurementDigitsRequest, ConfigureMeasurementDigitsResponse, ReadRequest, ReadResponse, CloseRequest, CloseResponse
from driver_pb2_grpc import InstrumentInteractionServicer

_SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "_visa_dmm_sim.yaml"
_RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}

class Function(Enum):
    """Enum that represents the measurement function."""

    DC_VOLTS = 0
    AC_VOLTS = 1


_FUNCTION_TO_VALUE = {
    Function.DC_VOLTS: "VOLT:DC",
    Function.AC_VOLTS: "VOLT:AC",
}

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


class DriverService(InstrumentInteractionServicer):

    def __init__(self):
        self._session = None

    def Initialize(self, request: InitializeRequest, context: grpc.ServicerContext) -> InitializeResponse:
        visa_library = f"{_SIMULATION_YAML_PATH}@sim" if request.simulate else ""
        resource_manager = pyvisa.ResourceManager(visa_library)

        session = resource_manager.open_resource(
            request.resource_name, read_termination="\n", write_termination="\n"
        )

        if not isinstance(session, pyvisa.resources.MessageBasedResource):
            raise grpc.RpcError("The 'session' object must be an instance of MessageBasedResource.")
        self._session = session

        if request.id_query:
            self._validate_id()

        if request.reset_device:
            self._reset()
        return InitializeResponse(is_initialized=True)

    def ConfigureMeasurementDigits(self, request: ConfigureMeasurementDigitsRequest, context: grpc.ServicerContext) -> ConfigureMeasurementDigitsResponse:
        if not self._session:
            raise grpc.RpcError("The session is not initialized yet. Please initialize the instrument before use.")
        function_enum = _FUNCTION_TO_VALUE[Function(request.function)]
        resolution_value = _RESOLUTION_DIGITS_TO_VALUE[str(request.resolution_digits)]

        self._session.write("CONF:%s %.g,%.g" % (function_enum, request.range, resolution_value))
        self._check_error()
        return ConfigureMeasurementDigitsResponse()

    def Read(self, request: ReadRequest, context: grpc.ServicerContext) -> ReadResponse:
        if not self._session:
            raise grpc.RpcError("The session is not initialized yet. Please initialize the instrument before use.")
        response = self._session.query("READ?")
        self._check_error()
        return ReadResponse(value=float(response))

    def Close(self, request: CloseRequest, context: grpc.ServicerContext) -> CloseResponse:
        if not self._session:
            raise grpc.RpcError("The session is not initialized yet. Please initialize the instrument before use.")
        self._session.close()
        self._session = None
        return CloseResponse()
    
    def _check_error(self) -> None:
        """Query the instrument's error queue."""
        response = self._session.query("SYST:ERR?")
        fields = response.split(",", maxsplit=1)
        assert len(fields) >= 1
        if int(fields[0]) != 0:
            raise RuntimeError("Instrument returned error %s: %s" % (fields[0], fields[1]))

    def _reset(self) -> None:
        """Reset the instrument to a known state."""
        self._session.write("*CLS")
        self._session.write("*RST")
        self._check_error()

    def _validate_id(self) -> None:
        """Check the selected instrument is proper and responding.."""
        instrument_id = self._session.query("*IDN?")
        if not any(id_check in instrument_id for id_check in _SUPPORTED_INSTRUMENT_IDS):
            raise RuntimeError(
                "The ID query failed. This may mean that you selected the wrong instrument, your instrument did not respond, "
                f"or you are using a model that is not officially supported by this driver. Instrument ID: {instrument_id}"
            )

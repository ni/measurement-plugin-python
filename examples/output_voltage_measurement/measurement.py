""" Source DC voltage as input with an NI SMU and measure output using NI-VISA DMM."""

import logging
import pathlib
import threading
import time
from typing import Tuple

import _visa_dmm
import click
import grpc
import hightime
import ni_measurementlink_service as nims
import nidcpower
import nidcpower.session
from _helpers import configure_logging, verbosity_option
from decouple import AutoConfig
from ni_measurementlink_service.session_management import SessionInformation

_NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
_NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933
_NIDCPOWER_TIMEOUT_ERROR_CODES = [
    _NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE,
    _NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE,
]

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "OutputVoltageMeasurement.serviceconfig",
    version="1.0.0.0",
    ui_file_paths=[service_directory / "OutputVoltageMeasurement.measui"],
)

# Search for the `.env` file starting with the current directory.
_config = AutoConfig(str(pathlib.Path.cwd()))
_VISA_DMM_SIMULATE: bool = _config("MEASUREMENTLINK_VISA_DMM_SIMULATE", default=False, cast=bool)


@measurement_service.register_measurement
# NI-DCPower configuration
@measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
@measurement_service.configuration("voltage_level_range", nims.DataType.Double, 6.0)
@measurement_service.configuration("current_limit", nims.DataType.Double, 0.01)
@measurement_service.configuration("current_limit_range", nims.DataType.Double, 0.01)
@measurement_service.configuration("source_delay", nims.DataType.Double, 0.0)
@measurement_service.configuration(
    "input_pin",
    nims.DataType.Pin,
    "InPin",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
# NI-VISA DMM configuration
@measurement_service.configuration(
    "measurement_type",
    nims.DataType.Enum,
    _visa_dmm.Function.DC_VOLTS,
    enum_type=_visa_dmm.Function,
)
@measurement_service.configuration("range", nims.DataType.Double, 1.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 3.5)
@measurement_service.configuration(
    "output_pin",
    nims.DataType.Pin,
    "OutPin",
    instrument_type=_visa_dmm.INSTRUMENT_TYPE_VISA_DMM,
)
@measurement_service.output("measured_value", nims.DataType.Double)
def measure(
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
    input_pin: str,
    measurement_type: _visa_dmm.Function,
    range: float,
    resolution_digits: float,
    output_pin: str,
) -> Tuple[float]:
    """Source DC voltage as input with an NI SMU and measure output using NI-VISA DMM."""
    logging.info(
        "Executing measurement: pin_names=%s voltage_level=%g measurement_type=%s range=%g resolution_digits=%g",
        [input_pin, output_pin],
        voltage_level,
        measurement_type,
        range,
        resolution_digits,
    )

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    with measurement_service.context.reserve_sessions([input_pin, output_pin]) as reservation:
        with reservation.create_nidcpower_session(), reservation.create_session(
            _create_visa_dmm_session, _visa_dmm.INSTRUMENT_TYPE_VISA_DMM
        ):
            # Configure the SMU channel connected to the input pin.
            source_connection = reservation.get_nidcpower_connection(input_pin)
            source_channel = source_connection.session.channels[source_connection.channel_name]
            source_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
            source_channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            source_channel.current_limit = current_limit
            source_channel.voltage_level_range = voltage_level_range
            source_channel.current_limit_range = current_limit_range
            source_channel.source_delay = hightime.timedelta(seconds=source_delay)
            source_channel.voltage_level = voltage_level

            # Configure the DMM connected to the output pin.
            measure_connection = reservation.get_connection(_visa_dmm.Session, output_pin)
            measure_session = measure_connection.session
            measure_session.configure_measurement_digits(measurement_type, range, resolution_digits)

            # Initiate the source channel to start sourcing a voltage on the
            # input pin. initiate() returns a context manager that aborts the
            # measurement when the function returns or raises an exception.
            with source_channel.initiate():
                # Wait for the output to settle.
                timeout = source_delay + 10.0
                _wait_for_nidcpower_event(
                    source_channel,
                    cancellation_event,
                    nidcpower.enums.Event.SOURCE_COMPLETE,
                    timeout,
                )

            # Measure the voltage on the output pin.
            measured_value = measure_session.read()

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


def _create_visa_dmm_session(session_info: SessionInformation) -> _visa_dmm.Session:
    # When this measurement is called from outside of TestStand (session_exists
    # == False), reset the instrument to a known state. In TestStand,
    # ProcessSetup resets the instrument.
    return _visa_dmm.Session(
        session_info.resource_name,
        reset_device=not session_info.session_exists,
        simulate=_VISA_DMM_SIMULATE,
    )


def _wait_for_nidcpower_event(
    channels: nidcpower.session._SessionBase,
    cancellation_event: threading.Event,
    event_id: nidcpower.enums.Event,
    timeout: float,
) -> None:
    """Wait for a NI-DCPower event or until error/cancellation occurs."""
    grpc_deadline = time.time() + measurement_service.context.time_remaining
    user_deadline = time.time() + timeout

    while True:
        if time.time() > user_deadline:
            raise TimeoutError("User timeout expired.")
        if time.time() > grpc_deadline:
            measurement_service.context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED, "Deadline exceeded."
            )
        if cancellation_event.is_set():
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

        # Wait for the NI-DCPower event. If this takes more than 100 ms, check
        # whether the measurement was canceled and try again. NI-DCPower does
        # not support canceling a call to wait_for_event().
        try:
            channels.wait_for_event(event_id, timeout=100e-3)
            break
        except nidcpower.errors.DriverError as e:
            if e.code in _NIDCPOWER_TIMEOUT_ERROR_CODES:
                pass
            raise


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Source DC voltage as input with an NI SMU and measure output using NI-VISA DMM."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

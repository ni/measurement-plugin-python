"""Source and measure a DC voltage with an NI SMU via an NI-SWITCH multiplexer."""

from __future__ import annotations

import logging
import pathlib
import sys
import threading
import time
from typing import TYPE_CHECKING, NamedTuple

import click
import grpc
import hightime
import ni_measurement_plugin_sdk_service as nims
import nidcpower
import nidcpower.session
import niswitch.session
from _helpers import configure_logging, verbosity_option

_NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
_NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933
_NIDCPOWER_TIMEOUT_ERROR_CODES = [
    _NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE,
    _NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE,
]

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDCPowerSourceDCVoltageWithMultiplexer.serviceconfig",
    ui_file_paths=[service_directory / "NIDCPowerSourceDCVoltageWithMultiplexer.measui"],
)

if TYPE_CHECKING:
    # The nidcpower Measurement named tuple doesn't support type annotations:
    # https://github.com/ni/nimi-python/issues/1885
    class _Measurement(NamedTuple):
        voltage: float
        current: float
        in_compliance: bool
        channel: str


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name",
    nims.DataType.IOResource,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
@measurement_service.configuration("voltage_level_range", nims.DataType.Double, 6.0)
@measurement_service.configuration("current_limit", nims.DataType.Double, 0.01)
@measurement_service.configuration("current_limit_range", nims.DataType.Double, 0.01)
@measurement_service.configuration("source_delay", nims.DataType.Double, 0.0)
@measurement_service.output("voltage_measurement", nims.DataType.Double)
@measurement_service.output("current_measurement", nims.DataType.Double)
def measure(
    pin_name: str,
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
) -> tuple[float, float]:
    """Source and measure a DC voltage with an NI SMU connected via an NI-SWITCH multiplexer."""
    logging.info("Executing measurement: pin_name=%s voltage_level=%g", pin_name, voltage_level)

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    with measurement_service.context.reserve_session(pin_name) as reservation:
        with reservation.initialize_nidcpower_session(), reservation.initialize_niswitch_multiplexer_session():
            # Configure the SMU channel connected to the input pin.
            connection = reservation.get_nidcpower_connection_with_multiplexer(
                niswitch.Session, pin_name
            )
            source_channel = connection.session.channels[connection.channel_name]
            source_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
            source_channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            source_channel.current_limit = current_limit
            source_channel.voltage_level_range = voltage_level_range
            source_channel.current_limit_range = current_limit_range
            source_channel.source_delay = hightime.timedelta(seconds=source_delay)
            source_channel.voltage_level = voltage_level

            # Connect the route in the NI-SWITCH multiplexer for the pin.
            connection.multiplexer_session.connect_multiple(connection.multiplexer_route)
            connection.multiplexer_session.wait_for_debounce()

            # Initiate the channels to start sourcing the outputs. initiate()
            # returns a context manager that aborts the measurement when the
            # function returns or raises an exception.
            with source_channel.initiate():
                # Wait for the outputs to settle.
                timeout = source_delay + 10.0
                _wait_for_nidcpower_event(
                    source_channel,
                    cancellation_event,
                    nidcpower.enums.Event.SOURCE_COMPLETE,
                    timeout,
                )

                measurement: _Measurement = source_channel.measure_multiple()[0]

            # Reset the channel to a known state
            source_channel.reset()

            # Disconnect the connected route.
            connection.multiplexer_session.disconnect_multiple(connection.multiplexer_route)
            connection.multiplexer_session.wait_for_debounce()

    logging.info(
        "Completed measurement measured voltage=%g measured current=%g",
        measurement.voltage,
        measurement.current,
    )
    return (
        measurement.voltage,
        measurement.current,
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
    """Source and measure a DC voltage with an NI SMU connected via an NI-SWITCH multiplexer."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

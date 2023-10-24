"""Source and measure a DC voltage with an NI SMU."""

from __future__ import annotations

import logging
import pathlib
import sys
import threading
import time
from typing import TYPE_CHECKING, Iterable, List, NamedTuple, Tuple

import click
import grpc
import hightime
import ni_measurementlink_service as nims
import nidcpower
import nidcpower.session
from _helpers import configure_logging, verbosity_option
from ni_measurementlink_service.session_management import TypedConnection

_NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
_NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933
_NIDCPOWER_TIMEOUT_ERROR_CODES = [
    _NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE,
    _NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE,
]

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDCPowerSourceDCVoltage.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory / "NIDCPowerSourceDCVoltage.measui",
        service_directory / "NIDCPowerSourceDCVoltageUI.vi",
    ],
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
    "pin_names",
    nims.DataType.PinArray1D,
    ["Pin1"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
@measurement_service.configuration("voltage_level_range", nims.DataType.Double, 6.0)
@measurement_service.configuration("current_limit", nims.DataType.Double, 0.01)
@measurement_service.configuration("current_limit_range", nims.DataType.Double, 0.01)
@measurement_service.configuration("source_delay", nims.DataType.Double, 0.0)
@measurement_service.output("measurement_sites", nims.DataType.Int32Array1D)
@measurement_service.output("measurement_pin_names", nims.DataType.StringArray1D)
@measurement_service.output("voltage_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("current_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("in_compliance", nims.DataType.BooleanArray1D)
def measure(
    pin_names: Iterable[str],
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
) -> Tuple[List[int], List[str], List[float], List[float], List[bool]]:
    """Source and measure a DC voltage with an NI SMU."""
    logging.info("Executing measurement: pin_names=%s voltage_level=%g", pin_names, voltage_level)

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    with measurement_service.context.reserve_session(pin_names) as reservation:
        with reservation.initialize_nidcpower_session() as session_info:
            # Use connections to map pin names to channel names. This sets the
            # channel order based on the pin order and allows mapping the
            # resulting measurements back to the corresponding pins and sites.
            connections = reservation.get_nidcpower_connections(pin_names)
            channel_order = ",".join(connection.channel_name for connection in connections)
            channels = session_info.session.channels[channel_order]

            # Configure the same settings for all of the channels corresponding
            # to the selected pins and sites.
            channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
            channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            channels.current_limit = current_limit
            channels.voltage_level_range = voltage_level_range
            channels.current_limit_range = current_limit_range
            channels.source_delay = hightime.timedelta(seconds=source_delay)
            channels.voltage_level = voltage_level

            # Initiate the channels to start sourcing the outputs. initiate()
            # returns a context manager that aborts the measurement when the
            # function returns or raises an exception.
            with channels.initiate():
                # Wait for the outputs to settle.
                timeout = source_delay + 10.0
                _wait_for_event(
                    channels, cancellation_event, nidcpower.enums.Event.SOURCE_COMPLETE, timeout
                )

                # Measure the voltage and current for each output.
                measurements: List[_Measurement] = channels.measure_multiple()

                # Determine whether the outputs are in compliance.
                for index, connection in enumerate(connections):
                    channel = connection.session.channels[connection.channel_name]
                    in_compliance = channel.query_in_compliance()
                    measurements[index] = measurements[index]._replace(in_compliance=in_compliance)

    _log_measurements(connections, measurements)
    logging.info("Completed measurement")
    return (
        [connection.site for connection in connections],
        [connection.pin_or_relay_name for connection in connections],
        [measurement.voltage for measurement in measurements],
        [measurement.current for measurement in measurements],
        [measurement.in_compliance for measurement in measurements],
    )


def _wait_for_event(
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


def _log_measurements(
    connections: Iterable[TypedConnection[nidcpower.Session]],
    measured_values: Iterable[_Measurement],
) -> None:
    """Log the measured values."""
    for connection, measurement in zip(connections, measured_values):
        logging.info("site%s/%s:", connection.site, connection.pin_or_relay_name)
        logging.info("  Voltage: %g V", measurement.voltage)
        logging.info("  Current: %g A", measurement.current)
        logging.info("  In compliance: %s", str(measurement.in_compliance))


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Source and measure a DC voltage with an NI SMU."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

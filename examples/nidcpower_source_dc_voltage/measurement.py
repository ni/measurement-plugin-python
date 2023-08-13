"""Source and measure a DC voltage with an NI SMU."""

import logging
import pathlib
import time
from typing import Iterable

import click
import grpc
import hightime
import nidcpower
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_grpc_device_channel,
    get_service_options,
    grpc_device_options,
    use_simulation_option,
    verbosity_option,
)
from _nidcpower_helpers import create_session
from _constants import USE_SIMULATION

import ni_measurementlink_service as nims

NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDCPowerSourceDCVoltage.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory / "NIDCPowerSourceDCVoltage.measui",
        service_directory / "NIDCPowerSourceDCVoltageUI.vi",
    ],
)
service_options = ServiceOptions()

RESERVATION_TIMEOUT_IN_SECONDS = 60.0
"""
If another measurement is using the session, the reserve function will wait
for it to complete. Specify a reservation timeout to aid in debugging missed
unreserve calls. Long measurements may require a longer timeout.
"""


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
):
    """Source and measure a DC voltage with an NI SMU."""
    logging.info("Executing measurement: pin_names=%s voltage_level=%g", pin_names, voltage_level)

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
        timeout=RESERVATION_TIMEOUT_IN_SECONDS,
    ) as reservation:
        grpc_device_channel = get_grpc_device_channel(
            measurement_service, nidcpower, service_options
        )
        with create_session(reservation.session_info, grpc_device_channel) as session:
            channels = session.channels[reservation.session_info.channel_list]
            channel_mappings = reservation.session_info.channel_mappings

            pending_cancellation = False

            def cancel_callback():
                logging.info("Canceling measurement")
                session_to_abort = session
                if session_to_abort is not None:
                    nonlocal pending_cancellation
                    pending_cancellation = True
                    session_to_abort.abort()

            measurement_service.context.add_cancel_callback(cancel_callback)
            time_remaining = measurement_service.context.time_remaining

            channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
            channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            channels.current_limit = current_limit
            channels.voltage_level_range = voltage_level_range
            channels.current_limit_range = current_limit_range
            channels.source_delay = hightime.timedelta(seconds=source_delay)
            channels.voltage_level = voltage_level
            # The Measurement named tuple doesn't support type annotations:
            # https://github.com/ni/nimi-python/issues/1885
            measured_values = []
            with channels.initiate():
                deadline = time.time() + time_remaining
                while True:
                    if time.time() > deadline:
                        measurement_service.context.abort(
                            grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded"
                        )
                    if pending_cancellation:
                        measurement_service.context.abort(
                            grpc.StatusCode.CANCELLED, "client requested cancellation"
                        )
                    try:
                        channels.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE, timeout=0.1)
                        break
                    except nidcpower.errors.DriverError as e:
                        """
                        There is no native way to support cancellation when taking a DCPower
                        measurement. To support cancellation, we will be calling WaitForEvent
                        until it succeeds or we have gone past the specified timeout. WaitForEvent
                        will throw an exception if it times out, which is why we are catching
                        and doing nothing.
                        """
                        if (
                            e.code == NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE
                            or e.code == NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE
                        ):
                            pass
                        else:
                            raise

                measured_values = channels.measure_multiple()
                for index, mapping in enumerate(channel_mappings):
                    measured_values[index] = measured_values[index]._replace(
                        in_compliance=session.channels[mapping.channel].query_in_compliance()
                    )
            session = None  # Don't abort after this point

    _log_measured_values(channel_mappings, measured_values)
    logging.info("Completed measurement")
    return (
        [m.site for m in channel_mappings],
        [m.pin_or_relay_name for m in channel_mappings],
        [m.voltage for m in measured_values],
        [m.current for m in measured_values],
        [m.in_compliance for m in measured_values],
    )


def _log_measured_values(
    channel_mappings: Iterable[nims.session_management.ChannelMapping],
    measured_values: Iterable,
):
    """Log the measured values."""
    for mapping, measurement in zip(channel_mappings, measured_values):
        logging.info("site%s/%s:", mapping.site, mapping.pin_or_relay_name)
        logging.info("  Voltage: %g V", measurement.voltage)
        logging.info("  Current: %g A", measurement.current)
        logging.info("  In compliance: %s", str(measurement.in_compliance))


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Source and measure a DC voltage with an NI SMU."""
    configure_logging(verbosity)

    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

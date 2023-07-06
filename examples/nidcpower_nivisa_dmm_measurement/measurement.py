import logging
import pathlib
import time
from typing import Iterable

import click
import grpc
import hightime
import nidcpower

import ni_measurementlink_service as nims


from enum import Enum

import pyvisa
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
from _nidcpower_helpers import USE_SIMULATION, create_session
from _visa_helpers import (
    INSTRUMENT_TYPE_DMM_SIMULATOR,
    USE_SIMULATION,
    check_instrument_error,
    create_visa_resource_manager,
    create_visa_session,
    log_instrument_id,
    reset_instrument,
)

NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933
RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory
    / "nidcpower_nivisa_dmm_measurement.serviceconfig",
    version="1.0.0.0",
    ui_file_paths=[service_directory / "nidcpower_nivisa_dmm_measurement.measui"],
)

service_options = ServiceOptions()

RESERVATION_TIMEOUT_IN_SECONDS = 60.0
"""
If another measurement is using the session, the reserve function will wait
for it to complete. Specify a reservation timeout to aid in debugging missed
unreserve calls. Long measurements may require a longer timeout.
"""


class Function(Enum):
    """Function that represents the measurement type."""

    DC_VOLTS = 0
    AC_VOLTS = 1


FUNCTION_TO_VALUE = {
    Function.DC_VOLTS: "VOLT:DC",
    Function.AC_VOLTS: "VOLT:AC",
}


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
    "measurement_type", nims.DataType.Enum, Function.DC_VOLTS, enum_type=Function
)
@measurement_service.configuration("range", nims.DataType.Double, 1.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 3.5)
@measurement_service.configuration(
    "output_pin",
    nims.DataType.Pin,
    "OutPin",
    instrument_type=INSTRUMENT_TYPE_DMM_SIMULATOR,
)
@measurement_service.output("measured_value", nims.DataType.Double)
def measure(
    # NI-DCPower configuration
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
    input_pin: str,
    # NI-VISA DMM configuration
    measurement_type:Function,
    range: float,
    resolution_digits: float,
    output_pin: str,
):
    session_management_client = create_session_management_client(measurement_service)
    # Creates NI-DCPower session.
    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[input_pin],
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
    ) as reservation:
        grpc_device_channel = get_grpc_device_channel(
            measurement_service, nidcpower, service_options
        )
        with create_session(reservation.session_info, grpc_device_channel) as source_session:
            channels = source_session.channels[reservation.session_info.channel_list]
            channel_mappings = reservation.session_info.channel_mappings

            pending_cancellation = False

            def cancel_callback():
                logging.info("Canceling measurement")
                session_to_abort = source_session
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
                        channels.wait_for_event(
                            nidcpower.enums.Event.SOURCE_COMPLETE, timeout=0.1
                        )
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
                        in_compliance=source_session.channels[
                            mapping.channel
                        ].query_in_compliance()
                    )
            source_session = None  # Don't abort after this point

    _log_measured_source_values(channel_mappings, measured_values)

    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[output_pin],
        instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
    ) as reservation:
        resource_manager = create_visa_resource_manager(service_options.use_simulation)
        with create_visa_session(
            resource_manager, reservation.session_info.resource_name
        ) as measure_session:
            # Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation for Resource
            # context manager implicitly upcasts derived class to base class
            assert isinstance(measure_session, pyvisa.resources.MessageBasedResource)

            log_instrument_id(measure_session)

            # When this measurement is called from outside of TestStand (session_exists == False),
            # reset the instrument to a known state. In TestStand, ProcessSetup resets the
            # instrument.
            if not reservation.session_info.session_exists:
                reset_instrument(measure_session)

            function_enum = FUNCTION_TO_VALUE[measurement_type]
            resolution_value = RESOLUTION_DIGITS_TO_VALUE[str(resolution_digits)]
            measure_session.write("CONF:%s %.g,%.g" % (function_enum, range, resolution_value))
            check_instrument_error(measure_session)

            response = measure_session.query("READ?")
            check_instrument_error(measure_session)
            measured_value = float(response)

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


def _log_measured_source_values(
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

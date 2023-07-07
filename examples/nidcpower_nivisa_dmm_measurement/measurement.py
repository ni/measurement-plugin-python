import logging
import pathlib
from typing import Iterable
import click
import hightime
import nidcpower
import pyvisa
import ni_measurementlink_service as nims

from enum import Enum
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_grpc_device_channel,
    get_service_options,
    grpc_device_options,
    use_simulation_option,
    verbosity_option,
    get_session_and_channel_for_pin,
)
from _nidcpower_helpers import (
    USE_SIMULATION,
    create_session,
    wait_for_source_complete_event,
)
from _visa_helpers import (
    INSTRUMENT_TYPE_DMM_SIMULATOR,
    USE_SIMULATION,
    check_instrument_error,
    create_visa_resource_manager,
    create_visa_session,
    log_instrument_id,
    reset_instrument,
)

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
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
    input_pin: str,
    measurement_type: Function,
    range: float,
    resolution_digits: float,
    output_pin: str,
):
    """Source DC voltage as input with an NI SMU and measure output using NI-VISA and an NI Instrument Simulator v2.0."""
    logging.info(
        "Executing measurement: pin_names=%s voltage_level=%g measurement_type=%s range=%g resolution_digits=%g",
        [input_pin, output_pin],
        voltage_level,
        measurement_type,
        range,
        resolution_digits,
    )

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_sessions(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[input_pin, output_pin],
        timeout=RESERVATION_TIMEOUT_IN_SECONDS,
    ) as reservation:
        grpc_device_channel = get_grpc_device_channel(
            measurement_service, nidcpower, service_options
        )
        source_session_info = get_session_info_from_pin(
            reservation.session_info, input_pin
        )
        measure_session_info = get_session_info_from_pin(
            reservation.session_info, output_pin
        )
        resource_manager = create_visa_resource_manager(service_options.use_simulation)
        # Creates NI-DCPower and NI-VISA DMM sessions.
        with create_session(
            source_session_info, grpc_device_channel
        ) as source_session, create_visa_session(
            resource_manager, measure_session_info.resource_name
        ) as measure_session:
            pending_cancellation = False
            add_cancel_callback(
                source_session, measurement_service, pending_cancellation
            )
            
            assert isinstance(measure_session, pyvisa.resources.MessageBasedResource)

            log_instrument_id(measure_session)

            # When this measurement is called from outside of TestStand (session_exists == False),
            # reset the instrument to a known state. In TestStand, ProcessSetup resets the
            # instrument.
            if not measure_session_info.session_exists:
                reset_instrument(measure_session)
            # Source input pin
            channels = source_session.channels[source_session_info.channel_list]

            channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
            channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
            channels.current_limit = current_limit
            channels.voltage_level_range = voltage_level_range
            channels.current_limit_range = current_limit_range
            channels.source_delay = hightime.timedelta(seconds=source_delay)
            channels.voltage_level = voltage_level
            with channels.initiate():
                wait_for_source_complete_event(
                    measurement_service, channels, pending_cancellation
                )

            # Configure and measure output pin using NI-VISA DMM
            function_enum = FUNCTION_TO_VALUE[measurement_type]
            resolution_value = RESOLUTION_DIGITS_TO_VALUE[str(resolution_digits)]
            measure_session.write(
                "CONF:%s %.g,%.g" % (function_enum, range, resolution_value)
            )
            check_instrument_error(measure_session)

            response = measure_session.query("READ?")
            check_instrument_error(measure_session)
            measured_value = float(response)

            source_session = None  # Don't abort after this point

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


def get_session_info_from_pin(session_info, pin_name):
    session_index = get_session_and_channel_for_pin(session_info, pin_name)[0]
    return session_info[session_index]


def add_cancel_callback(session, measurement_service, pending_cancellation):
    def cancel_callback():
        session_to_abort = session
        if session_to_abort is not None:
            nonlocal pending_cancellation
            pending_cancellation = True
            session_to_abort.abort()

    measurement_service.context.add_cancel_callback(cancel_callback)


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

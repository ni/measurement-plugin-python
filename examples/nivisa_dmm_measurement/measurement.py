"""Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""

import logging
import pathlib
from enum import Enum
from typing import Tuple

import click
import grpc
import pyvisa.resources
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_service_options,
    use_simulation_option,
    verbosity_option,
)
from _visa_helpers import (
    INSTRUMENT_TYPE_DMM_SIMULATOR,
    check_instrument_error,
    create_visa_resource_manager,
    create_visa_session,
    log_instrument_id,
    reset_instrument,
)

import ni_measurementlink_service as nims

# To use NI Instrument Simulator v2.0 hardware, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIVisaDmmMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIVisaDmmMeasurement.measui"],
)
service_options = ServiceOptions()


RESOLUTION_DIGITS_TO_VALUE = {"3.5": 0.001, "4.5": 0.0001, "5.5": 1e-5, "6.5": 1e-6}


class Function(Enum):
    """Function that represents the measurement type."""

    DC_VOLTS = 0
    AC_VOLTS = 1


FUNCTION_TO_VALUE = {
    Function.DC_VOLTS: "VOLT:DC",
    Function.AC_VOLTS: "VOLT:AC",
}


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name", nims.DataType.Pin, "Pin1", instrument_type=INSTRUMENT_TYPE_DMM_SIMULATOR
)
@measurement_service.configuration(
    "measurement_type", nims.DataType.Enum, Function.DC_VOLTS, enum_type=Function
)
@measurement_service.configuration("range", nims.DataType.Double, 1.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 3.5)
@measurement_service.output("measured_value", nims.DataType.Double)
def measure(
    pin_name: str,
    measurement_type: Function,
    range: float,
    resolution_digits: float,
) -> Tuple:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    logging.info(
        "Starting measurement: pin_name=%s measurement_type=%s range=%g resolution_digits=%g",
        pin_name,
        measurement_type,
        range,
        resolution_digits,
    )

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_sessions(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[pin_name],
        instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
        # If another measurement is using the session, wait for it to complete.
        # Specify a timeout to aid in debugging missed unreserve calls.
        # Long measurements may require a longer timeout.
        timeout=60,
    ) as reservation:
        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        resource_manager = create_visa_resource_manager(service_options.use_simulation)
        session_info = reservation.session_info[0]
        with create_visa_session(resource_manager, session_info.resource_name) as session:
            # Work around https://github.com/pyvisa/pyvisa/issues/739 - Type annotation for Resource
            # context manager implicitly upcasts derived class to base class
            assert isinstance(session, pyvisa.resources.MessageBasedResource)

            log_instrument_id(session)

            # When this measurement is called from outside of TestStand (session_exists == False),
            # reset the instrument to a known state. In TestStand, ProcessSetup resets the
            # instrument.
            if not session_info.session_exists:
                reset_instrument(session)

            function_enum = FUNCTION_TO_VALUE[measurement_type]
            resolution_value = RESOLUTION_DIGITS_TO_VALUE[str(resolution_digits)]
            session.write("CONF:%s %.g,%.g" % (function_enum, range, resolution_value))
            check_instrument_error(session)

            response = session.query("READ?")
            check_instrument_error(session)
            measured_value = float(response)

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


@click.command
@verbosity_option
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

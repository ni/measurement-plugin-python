"""Perform a DMM measurement using python-ivi."""

import contextlib
import logging
import pathlib
import sys
from typing import Tuple

import click
import grpc
import pyvisa
from _helpers import (
    ServiceOptions,
    configure_logging,
    get_service_options,
    str_to_enum,
    use_simulation_option,
    verbosity_option,
)

import ni_measurementlink_service as nims

try:
    # HACK: python-ivi expects to be able to import pyvisa using "import visa" as of the last
    # commit on 2/18/2017.
    sys.modules["visa"] = pyvisa
    import ivi
finally:
    pass

# To use a physical DMM instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "PythonIviDmmMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "PythonIviDmmMeasurement.measui"],
)
service_options = ServiceOptions()

INSTRUMENT_TYPE_AG34401A = "ag34401A"

FUNCTION_TO_ENUM = {
    "DC Volts": "dc_volts",
    "AC Volts": "ac_volts",
}

RESOLUTION_DIGITS_TO_VALUE = {
    "3.5": 0.001,
    "4.5": 0.0001,
    "5.5": 1e-5,
    "6.5": 1e-6,
}


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name", nims.DataType.Pin, "Pin1", instrument_type=INSTRUMENT_TYPE_AG34401A
)
@measurement_service.configuration("measurement_type", nims.DataType.String, "DC Volts")
@measurement_service.configuration("range", nims.DataType.Double, 1.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 3.5)
@measurement_service.output("measured_value", nims.DataType.Double)
def measure(
    pin_name: str,
    measurement_type: str,
    range: float,
    resolution_digits: float,
) -> Tuple:
    """Perform a DMM measurement using python-ivi."""
    logging.info(
        "Starting measurement: pin_name=%s measurement_type=%s range=%g resolution_digits=%g",
        pin_name,
        measurement_type,
        range,
        resolution_digits,
    )

    session_management_client = nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )

    with session_management_client.reserve_sessions(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[pin_name],
        instrument_type_id=INSTRUMENT_TYPE_AG34401A,
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

        session_info = reservation.session_info[0]
        # When this measurement is called from outside of TestStand (session_exists == False),
        # reset the instrument to a known state. In TestStand, ProcessSetup resets the instrument.
        with contextlib.closing(
            ivi.agilent.agilent34401A(
                session_info.resource_name,
                reset=not session_info.session_exists,
                simulate=service_options.use_simulation,
            )
        ) as session:
            try:
                logging.info("Instrument: %s", session.identity.instrument_model)

                session.configure(
                    function=str_to_enum(FUNCTION_TO_ENUM, measurement_type),
                    range=range,
                    resolution=str_to_enum(RESOLUTION_DIGITS_TO_VALUE, str(resolution_digits)),
                )

                measured_value = session.measurement.read(max_time=10.0)
            finally:
                # HACK: python-ivi doesn't close pyvisa sessions as of the last commit on 2/18/2017.
                if (
                    session is not None
                    and session._interface is not None
                    and session._interface.instrument is not None
                ):
                    session._interface.instrument.close()

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


@click.command
@verbosity_option
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Perform a DMM measurement using python-ivi."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

"""Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""

import logging
import pathlib
import sys
from typing import Any, Tuple

import click
from _constants import USE_SIMULATION
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_service_options,
    use_simulation_option,
    verbosity_option,
)
from _visa_dmm import INSTRUMENT_TYPE_DMM_SIMULATOR, Function, Session

import ni_measurementlink_service as nims

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIVisaDmmMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIVisaDmmMeasurement.measui"],
)
service_options = ServiceOptions()


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
) -> Tuple[float]:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    logging.info(
        "Starting measurement: pin_name=%s measurement_type=%s range=%g resolution_digits=%g",
        pin_name,
        measurement_type,
        range,
        resolution_digits,
    )

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[pin_name],
    ) as reservation:
        with Session(
            reservation.session_info.resource_name,
            use_simulation=service_options.use_simulation,
        ) as session:
            session.configure_measurement_digits(
                measurement_type, range, resolution_digits
            )
            measured_value = session.read()

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


@click.command
@verbosity_option
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs: Any) -> None:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

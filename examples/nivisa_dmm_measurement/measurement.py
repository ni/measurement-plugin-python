"""Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""

import logging
import pathlib
import sys

import click
import ni_measurement_plugin_sdk_service as nims
from _helpers import configure_logging, verbosity_option
from _visa_dmm import INSTRUMENT_TYPE_VISA_DMM, Function
from _visa_dmm_session_management import VisaDmmSessionConstructor
from decouple import AutoConfig

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIVisaDmmMeasurement.serviceconfig",
    ui_file_paths=[service_directory / "NIVisaDmmMeasurement.measui"],
)

# Search for the `.env` file starting with the current directory.
_config = AutoConfig(str(pathlib.Path.cwd()))


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name", nims.DataType.IOResource, "Pin1", instrument_type=INSTRUMENT_TYPE_VISA_DMM
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
) -> tuple[float]:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    logging.info(
        "Starting measurement: pin_name=%s measurement_type=%s range=%g resolution_digits=%g",
        pin_name,
        measurement_type,
        range,
        resolution_digits,
    )

    session_constructor = VisaDmmSessionConstructor(_config, measurement_service.discovery_client)

    with measurement_service.context.reserve_session(pin_name) as reservation:
        with reservation.initialize_session(
            session_constructor, INSTRUMENT_TYPE_VISA_DMM
        ) as session_info:
            session = session_info.session
            session.configure_measurement_digits(measurement_type, range, resolution_digits)
            measured_value = session.read()

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

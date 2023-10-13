"""Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""

import logging
import pathlib
import sys
from typing import Tuple

import click
import ni_measurementlink_service as nims
from _helpers import configure_logging, verbosity_option
from _visa_dmm import INSTRUMENT_TYPE_VISA_DMM, Function, Session
from decouple import AutoConfig
from ni_measurementlink_service.session_management import SessionInformation

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIVisaDmmMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIVisaDmmMeasurement.measui"],
)

# Search for the `.env` file starting with the current directory.
_config = AutoConfig(str(pathlib.Path.cwd()))
_VISA_DMM_SIMULATE: bool = _config("MEASUREMENTLINK_VISA_DMM_SIMULATE", default=False, cast=bool)


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name", nims.DataType.Pin, "Pin1", instrument_type=INSTRUMENT_TYPE_VISA_DMM
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

    with measurement_service.context.reserve_session(pin_name) as reservation:
        with reservation.create_session(_create_session, INSTRUMENT_TYPE_VISA_DMM) as session_info:
            session = session_info.session
            session.configure_measurement_digits(measurement_type, range, resolution_digits)
            measured_value = session.read()

    logging.info("Completed measurement: measured_value=%g", measured_value)
    return (measured_value,)


def _create_session(session_info: SessionInformation) -> Session:
    # When this measurement is called from outside of TestStand (session_exists
    # == False), reset the instrument to a known state. In TestStand,
    # ProcessSetup resets the instrument.
    return Session(
        session_info.resource_name,
        reset_device=not session_info.session_exists,
        simulate=_VISA_DMM_SIMULATE,
    )


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

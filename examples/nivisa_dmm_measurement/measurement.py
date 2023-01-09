"""Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""

import contextlib
import logging
import pathlib
import sys
from typing import Tuple

import click
import grpc
import pyvisa
import pyvisa.resources
import pyvisa.typing
from _helpers import str_to_enum

import ni_measurementlink_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="NI-VISA DMM Measurement (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NIVisaDmmMeasurement.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NIVisaDmmMeasurement_Python",
    description_url="",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)

INSTRUMENT_TYPE = "Instrument Simulator v2.0 DMM"

FUNCTION_TO_ENUM = {
    "DC Volts": "VOLT:DC",
    "AC Volts": "VOLT:AC",
}

RESOLUTION_VALUE = {
    3.5: 0.001,
    4.5: 0.0001,
    5.5: 1e-5,
    6.5: 1e-6,
}


@measurement_service.register_measurement
@measurement_service.configuration("pin_name", nims.DataType.Pin, "Pin1", instrument_type=INSTRUMENT_TYPE)
@measurement_service.configuration("measurement_type", nims.DataType.String, "DC Volts")
@measurement_service.configuration("range", nims.DataType.Double, 1.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 3.5)
@measurement_service.output("measured_value", nims.DataType.Double)
def measure(
    pin_name: str,
    measurement_type: str,
    range: float,
    resolution_digits: str,
) -> Tuple:
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
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

    with contextlib.ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_or_relay_names=[pin_name],
                instrument_type_id=INSTRUMENT_TYPE,
                timeout=-1,
            )
        )

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        resource_manager = pyvisa.ResourceManager()

        session_info = reservation.session_info[0]
        session = stack.enter_context(resource_manager.open_resource(session_info.resource_name))
        assert isinstance(session, pyvisa.resources.MessageBasedResource)

        instr_id = session.query("*IDN?")
        logging.info("Instrument id: %s", instr_id)

        session.write("CONF:%s %.g,%.g;" % (str_to_enum(FUNCTION_TO_ENUM, measurement_type), range, RESOLUTION_VALUE[resolution_digits]))
        _query_error()

        response = session.query("READ?")
        measured_value = float(response)
        _query_error()

    logging.info("Completed measurement")
    return (measured_value,)


def _query_error(session: pyvisa.resources.MessageBasedResource):
    response = session.query("SYST:ERR?")
    number, description = response.split(",")
    if int(number) != 0:
        logging.error("Instrument error: %s", response)
        assert description[0] == '"' and description[-1] == '"'
        raise RuntimeError("Instrument error %s: %s" % (number, description[1:-1]))


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def main(verbose: int):
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    sys.exit(main())

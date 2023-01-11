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
from _helpers import ServiceOptions, str_to_enum

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
service_options = ServiceOptions()

INSTRUMENT_TYPE_DMM_SIMULATOR = "DigitalMultimeterSimulator"
SIMULATION_YAML_PATH = pathlib.Path(__file__).resolve().parent / "NIInstrumentSimulatorV2_0.yaml"

FUNCTION_TO_ENUM = {
    "DC Volts": "VOLT:DC",
    "AC Volts": "VOLT:AC",
}

RESOLUTION_DIGITS_TO_VALUE = {
    "3.5": 0.001,
    "4.5": 0.0001,
    "5.5": 1e-5,
    "6.5": 1e-6,
}


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name", nims.DataType.Pin, "Pin1", instrument_type=INSTRUMENT_TYPE_DMM_SIMULATOR
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
                instrument_type_id=INSTRUMENT_TYPE_DMM_SIMULATOR,
                timeout=-1,
            )
        )

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        resource_manager = pyvisa.ResourceManager(
            f"{SIMULATION_YAML_PATH}@sim" if service_options.use_simulation else ""
        )

        session_info = reservation.session_info[0]
        session = stack.enter_context(
            _create_visa_session(resource_manager, session_info.resource_name)
        )

        instrument_id = session.query("*IDN?")
        logging.info("Instrument: %s", instrument_id)

        function_enum = str_to_enum(FUNCTION_TO_ENUM, measurement_type)
        resolution_value = str_to_enum(RESOLUTION_DIGITS_TO_VALUE, str(resolution_digits))
        session.write("CONF:%s %.g,%.g" % (function_enum, range, resolution_value))
        _query_error(session)

        response = session.query("READ?")
        measured_value = float(response)
        _query_error(session)

    logging.info("Completed measurement")
    return (measured_value,)


def _create_visa_session(
    resource_manager: pyvisa.ResourceManager, resource_name: str
) -> pyvisa.resources.MessageBasedResource:
    session = resource_manager.open_resource(resource_name)
    assert isinstance(session, pyvisa.resources.MessageBasedResource)
    # The NI Instrument Simulator hardware accepts either \r\n or \n but the simulation YAML needs
    # the newlines to match.
    session.read_termination = "\n"
    session.write_termination = "\n"
    return session


def _query_error(session: pyvisa.resources.MessageBasedResource):
    response = session.query("SYST:ERR?")
    fields = response.split(",", maxsplit=1)
    assert len(fields) >= 1
    if int(fields[0]) != 0:
        raise RuntimeError("Instrument returned error %s: %s" % (fields[0], fields[1]))


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
@click.option(
    "--use-simulation/--no-use-simulation",
    default=False,
    is_flag=True,
    help="Use simulated instruments.",
)
def main(verbose: int, use_simulation: bool):
    """Perform a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    global service_options
    service_options = ServiceOptions(use_simulation=use_simulation)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    sys.exit(main())

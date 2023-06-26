"""Perform a measurement using an NI DMM."""

import logging
import math
import pathlib
from enum import Enum
from typing import Tuple

import click
import nidmm
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
from _nidmm_helpers import USE_SIMULATION, create_session

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDmmMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIDmmMeasurement.measui"],
)
service_options = ServiceOptions()

# If another measurement is using the session, the reserve function will wait
# for it to complete. Specify a reservation timeout to aid in debugging missed
# unreserve calls. Long measurements may require a longer timeout.
RESERVATION_TIMEOUT_IN_SECONDS = 60.0


class Function(Enum):
    """Wrapper enum that contains a zero value."""

    NONE = 0
    DC_VOLTS = nidmm.Function.DC_VOLTS.value
    AC_VOLTS = nidmm.Function.AC_VOLTS.value
    DC_CURRENT = nidmm.Function.DC_CURRENT.value
    AC_CURRENT = nidmm.Function.AC_CURRENT.value
    TWO_WIRE_RES = nidmm.Function.TWO_WIRE_RES.value
    FOUR_WIRE_RES = nidmm.Function.FOUR_WIRE_RES.value
    FREQ = nidmm.Function.FREQ.value
    PERIOD = nidmm.Function.PERIOD.value
    TEMPERATURE = nidmm.Function.TEMPERATURE.value
    AC_VOLTS_DC_COUPLED = nidmm.Function.AC_VOLTS_DC_COUPLED.value
    DIODE = nidmm.Function.DIODE.value
    WAVEFORM_VOLTAGE = nidmm.Function.WAVEFORM_VOLTAGE.value
    WAVEFORM_CURRENT = nidmm.Function.WAVEFORM_CURRENT.value
    CAPACITANCE = nidmm.Function.CAPACITANCE.value
    INDUCTANCE = nidmm.Function.INDUCTANCE.value


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name",
    nims.DataType.Pin,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DMM,
)
@measurement_service.configuration(
    "measurement_type", nims.DataType.Enum, Function.DC_VOLTS, enum_type=Function
)
@measurement_service.configuration("range", nims.DataType.Double, 10.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 5.5)
@measurement_service.output("measured_value", nims.DataType.Double)
@measurement_service.output("signal_out_of_range", nims.DataType.Boolean)
@measurement_service.output("absolute_resolution", nims.DataType.Double)
def measure(
    pin_name: str,
    measurement_type: Function,
    range: float,
    resolution_digits: float,
) -> Tuple:
    """Perform a measurement using an NI DMM."""
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
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DMM,
        timeout=RESERVATION_TIMEOUT_IN_SECONDS,
    ) as reservation:
        grpc_device_channel = get_grpc_device_channel(measurement_service, nidmm, service_options)
        with create_session(reservation.session_info, grpc_device_channel) as session:
            session.configure_measurement_digits(
                nidmm.Function(measurement_type.value)
                if measurement_type != Function.NONE
                else nidmm.Function.DC_VOLTS,
                range,
                resolution_digits,
            )
            measured_value = session.read()
            signal_out_of_range = math.isnan(measured_value) or math.isinf(measured_value)
            absolute_resolution = session.resolution_absolute

    logging.info(
        "Completed measurement: measured_value=%g signal_out_of_range=%s absolute_resolution=%g",
        measured_value,
        signal_out_of_range,
        absolute_resolution,
    )
    return (measured_value, signal_out_of_range, absolute_resolution)


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Perform a measurement using an NI DMM."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

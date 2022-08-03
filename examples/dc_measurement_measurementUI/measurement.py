"""User Measurement.

User can Import driver and 3rd Party Packages based on requirements.

"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

import click
import hightime
import nidcpower

import ni_measurement_service as nims


measurement_info = nims.MeasurementInfo(
    display_name="DCMeasurement(Py)",
    version="0.1.0.0",
    measurement_type="DC",
    product_type="ADC",
    ui_file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "DCMeasurement.measui"),
    ui_file_type=nims.UIFileType.MeasurementUI,
)

service_info = nims.ServiceInfo(
    service_class="DCMeasurement_Python",
    service_id="{825076C9-0484-4123-B360-81D29397824F}",
    description_url="https://www.ni.com/measurementservices/dcmeasurement.html",
)

dc_measurement_service = nims.MeasurementService(measurement_info, service_info)


@dc_measurement_service.register_measurement
@dc_measurement_service.configuration("Resource name", nims.DataType.String, "DPS_4145")
@dc_measurement_service.configuration("Voltage level(V)", nims.DataType.Float, 6.0)
@dc_measurement_service.configuration("Voltage level range(V)", nims.DataType.Float, 6.0)
@dc_measurement_service.configuration("Current limit(A)", nims.DataType.Float, 0.01)
@dc_measurement_service.configuration("Current limit range(A)", nims.DataType.Float, 0.01)
@dc_measurement_service.configuration("Source delay(s)", nims.DataType.Float, 0.0)
@dc_measurement_service.output("Voltage Measurement(V)", nims.DataType.Float)
@dc_measurement_service.output("Current Measurement(A)", nims.DataType.Float)
def measure(
    resource_name,
    voltage_level,
    voltage_level_range,
    current_limit,
    current_limit_range,
    source_delay,
):
    """User Measurement API. Returns Voltage Measurement as the only output.

    Returns
    -------
        Tuple of Output Variables, in the order configured in the metadata.py

    """
    # User Logic :
    print("Executing DCMeasurement(Py)")

    def cancel_callback():
        print("Canceling DCMeasurement(Py)")
        if session is not None:
            session.abort()

    dc_measurement_service.context.add_cancel_callback(cancel_callback)
    dc_measurement_service.context.set_deadline(datetime.now() + timedelta(minutes=5))
    
    timeout = hightime.timedelta(seconds=(source_delay + 1.0))
    with nidcpower.Session(resource_name=resource_name) as session:
        # Configure the session.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = voltage_level_range
        session.current_limit_range = current_limit_range
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.voltage_level = voltage_level
        measured_value = None
        with session.initiate():
            channel = session.get_channel_names("0")
            measured_value = session.channels[channel].fetch_multiple(count=1, timeout=timeout)
        session = None  # Don't abort after this point
    print_fetched_measurements(measured_value)
    measured_voltage = measured_value[0].voltage
    measured_current = measured_value[0].current
    print("Voltage Value:", measured_voltage)
    print("Current Value:", measured_current)
    print("---------------------------------")
    return [measured_voltage, measured_current]


def print_fetched_measurements(measurements):
    """Format and print the Measured Values."""
    layout = "{: >20} : {:f}{}"
    print("Fetched Measurement Values:")
    print(layout.format("Voltage", measurements[0].voltage, " V"))
    print(layout.format("Current", measurements[0].current, " A"))
    print(layout.format("In compliance", measurements[0].in_compliance, ""))


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
)
def main(verbose: int):
    """Host the DC Measurement (Screen UI) service."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    dc_measurement_service.host_service()
    input("Press enter to close the measurement service.\n")
    dc_measurement_service.close_service()


if __name__ == "__main__":
    sys.exit(main())

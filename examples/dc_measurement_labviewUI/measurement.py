"""User Measurement.

User can Import driver and 3rd Party Packages based on requirements.

"""

import logging
import os
import sys

import click
import hightime
import nidcpower

import ni_measurement_service as nims


measurement_info = nims.MeasurementInfo(
    display_name="DCMeasurement(Py_VI)",
    version="0.1.0.0",
    measurement_type="DC",
    product_type="ADC",
    ui_file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "DCMeasurementUI.vi"),
    ui_file_type=nims.UIFileType.LabVIEW,
)

service_info = nims.ServiceInfo(
    service_class="DCMeasurement_Python_VI",
    service_id="{B290B571-CB76-426F-9ACC-5168DC1B027B}",
    description_url="https://www.ni.com/measurementservices/dcmeasurement.html",
)
dc_measurement_service = nims.MeasurementService(measurement_info, service_info)


@dc_measurement_service.register_measurement
@dc_measurement_service.configuration("Resource name", nims.DataType.String, "DPS_4145")
@dc_measurement_service.configuration("Voltage level(V)", nims.DataType.Double, 6.0)
@dc_measurement_service.configuration("Voltage level range(V)", nims.DataType.Double, 6.0)
@dc_measurement_service.configuration("Current limit(A)", nims.DataType.Double, 0.01)
@dc_measurement_service.configuration("Current limit range(A)", nims.DataType.Double, 0.01)
@dc_measurement_service.configuration("Source delay(s)", nims.DataType.Double, 0.0)
@dc_measurement_service.output("Voltage Measurements(V)", nims.DataType.DoubleArray1D)
@dc_measurement_service.output("Current Measurements(A)", nims.DataType.DoubleArray1D)
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
            pending_cancellation = True
            session.abort()

    pending_cancellation = False
    dc_measurement_service.context.add_cancel_callback(cancel_callback)
    time_remaining = dc_measurement_service.context.time_remaining()

    timeout = hightime.timedelta(seconds=(min(time_remaining, source_delay + 1.0)))
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
        measured_values = []
        with session.initiate():
            channel = session.get_channel_names("0")
            for i in range(0, 5):
                if pending_cancellation:
                    break
                measured_values.append(
                    session.channels[channel].fetch_multiple(count=1, timeout=timeout)
                )
        session = None  # Don't abort after this point
    measured_voltages = []
    measured_currents = []
    for measured_value in measured_values:
        print_fetched_measurements(measured_value)
        measured_voltages.append(measured_value[0].voltage)
        measured_currents.append(measured_value[0].current)
        print("Voltage Value:", measured_value[0].voltage)
        print("Current Value:", measured_value[0].current)
        print("---------------------------------")
    return [measured_voltages, measured_currents]


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
    """Host the DC Measurement (LabVIEW UI) service."""
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

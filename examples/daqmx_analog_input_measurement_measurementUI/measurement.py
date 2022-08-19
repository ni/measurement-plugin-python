"""User Measurement.

User can Import driver and 3rd Party Packages based on requirements.

"""

import logging
import os
import sys

import click
import nidaqmx

import ni_measurement_service as nims


measurement_info = nims.MeasurementInfo(
    display_name="DAQmx Analog Input Measurement(Py)",
    version="0.1.0.0",
    measurement_type="DAQmx Analog Input",
    product_type="DAQ",
    ui_file_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "DAQmxAnalogInputMeasurement.measui"
    ),
    ui_file_type=nims.UIFileType.MeasurementUI,
)

service_info = nims.ServiceInfo(
    service_class="DAQmx_Analog_Input_Measurement_Python",
    service_id="{D8B7FF34-3532-4604-9EEE-B5AFC43B7909}",
    description_url="https://www.ni.com/measurementservices/daqmxmeasurement.html",
)

daqmx_analog_input_measurement_service = nims.MeasurementService(measurement_info, service_info)


@daqmx_analog_input_measurement_service.register_measurement
@daqmx_analog_input_measurement_service.configuration(
    "Physical Channel", nims.DataType.String, "Dev1/ai0"
)
@daqmx_analog_input_measurement_service.configuration("Sample Rate", nims.DataType.Double, 1000.0)
@daqmx_analog_input_measurement_service.configuration(
    "Number of Samples", nims.DataType.UInt64, 100
)
@daqmx_analog_input_measurement_service.output(
    "Voltage Measurements(V)", nims.DataType.DoubleArray1D
)
def measure(physical_channel, sample_rate, number_of_samples):
    """User Measurement API. Returns Voltage Measurement as the only output.

    Returns
    -------
        Tuple of Output Variables, in the order configured in the metadata.py

    """
    # User Logic :
    print("Executing DAQmx Analog Input Measurement(Py)")

    def cancel_callback():
        print("Canceling DAQmx Analog Input Measurement(Py)")
        if task is not None:
            task.control(nidaqmx.constants.TaskMode.TASK_ABORT)

    daqmx_analog_input_measurement_service.context.add_cancel_callback(cancel_callback)
    time_remaining = daqmx_analog_input_measurement_service.context.time_remaining()

    timeout = min(time_remaining, 10.0)
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(physical_channel)
        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            source="",
            active_edge=nidaqmx.constants.Edge.RISING,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
            samps_per_chan=number_of_samples,
        )
        voltage_values = task.read(number_of_samples_per_channel=number_of_samples, timeout=timeout)
        task = None  # Don't abort after this point

    for voltage_value in voltage_values:
        print("Voltage Value:", voltage_value)
        print("---------------------------------")
    return (voltage_values,)


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
)
def main(verbose: int):
    """Host the DAQmx Analog Input Measurement (Screen UI) service."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    daqmx_analog_input_measurement_service.host_service()
    input("Press enter to close the measurement service.\n")
    daqmx_analog_input_measurement_service.close_service()


if __name__ == "__main__":
    sys.exit(main())

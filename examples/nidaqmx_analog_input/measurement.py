"""Perform a finite analog input measurement with NI-DAQmx."""

import logging
import pathlib
import sys

import click
import nidaqmx

import ni_measurementlink_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="NI-DAQmx Analog Input (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NIDAQmxAnalogInput.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NIDAQmxAnalogInput_Python",
    description_url="",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)


@measurement_service.register_measurement
@measurement_service.configuration("physical_channel", nims.DataType.String, "Dev1/ai0")
@measurement_service.configuration("sample_rate", nims.DataType.Double, 1000.0)
@measurement_service.configuration("number_of_samples", nims.DataType.UInt64, 100)
@measurement_service.output("acquired_samples", nims.DataType.DoubleArray1D)
def measure(physical_channel, sample_rate, number_of_samples):
    """Perform a finite analog input measurement with NI-DAQmx."""
    logging.info(
        "Executing measurement: physical_channel=%s sample_rate=%g number_of_samples=%d",
        physical_channel,
        sample_rate,
        number_of_samples,
    )

    def cancel_callback():
        logging.info("Canceling measurement")
        task_to_abort = task
        if task_to_abort is not None:
            task_to_abort.control(nidaqmx.constants.TaskMode.TASK_ABORT)

    measurement_service.context.add_cancel_callback(cancel_callback)
    time_remaining = measurement_service.context.time_remaining

    timeout = min(time_remaining, 10.0)
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(physical_channel)
        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            samps_per_chan=number_of_samples,
        )
        voltage_values = task.read(number_of_samples_per_channel=number_of_samples, timeout=timeout)
        task = None  # Don't abort after this point

    _log_measured_values(voltage_values)
    logging.info("Completed measurement")
    return (voltage_values,)


def _log_measured_values(samples, max_samples_to_display=5):
    """Log the measured values."""
    if len(samples) > max_samples_to_display:
        for index, value in enumerate(samples[0 : max_samples_to_display - 1]):
            logging.info("Sample %d: %f", index, value)
        logging.info("...")
        logging.info("Sample %d: %f", len(samples) - 1, samples[-1])
    else:
        for index, value in enumerate(samples):
            logging.info("Sample %d: %f", index, value)


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
)
def main(verbose: int):
    """Perform a finite analog input measurement with NI-DAQmx."""
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

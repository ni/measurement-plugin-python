"""Perform a finite analog input measurement with NI-DAQmx."""

import logging
import pathlib

import click
import nidaqmx
from _helpers import configure_logging, verbosity_option

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDAQmxAnalogInput.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIDAQmxAnalogInput.measui"],
)


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
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a finite analog input measurement with NI-DAQmx."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

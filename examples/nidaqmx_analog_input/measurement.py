"""Perform a finite analog input measurement with NI-DAQmx."""

import logging
import pathlib
import sys

import click
import ni_measurement_plugin_sdk_service as nims
from _helpers import (
    configure_logging,
    verbosity_option,
)
from nidaqmx.constants import TaskMode

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDAQmxAnalogInput.serviceconfig",
    ui_file_paths=[service_directory / "NIDAQmxAnalogInput.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name",
    nims.DataType.IOResource,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DAQMX,
)
@measurement_service.configuration("sample_rate", nims.DataType.Double, 1000.0)
@measurement_service.configuration("number_of_samples", nims.DataType.UInt64, 100)
@measurement_service.output("acquired_samples", nims.DataType.DoubleArray1D)
def measure(pin_name: str, sample_rate: float, number_of_samples: int) -> tuple[list[float]]:
    """Perform a finite analog input measurement with NI-DAQmx."""
    logging.info(
        "Executing measurement: pin_name=%s sample_rate=%g number_of_samples=%d",
        pin_name,
        sample_rate,
        number_of_samples,
    )
    with measurement_service.context.reserve_session(pin_name) as reservation:
        with reservation.create_nidaqmx_task() as session_info:
            task = session_info.session

            def cancel_callback() -> None:
                logging.info("Canceling measurement")
                if (task_to_abort := task) is not None:
                    task_to_abort.control(TaskMode.TASK_ABORT)

            measurement_service.context.add_cancel_callback(cancel_callback)

            # If we created a new DAQmx task, we must also add channels to it.
            if not session_info.session_exists:
                task.ai_channels.add_ai_voltage_chan(session_info.channel_list)

            task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                samps_per_chan=number_of_samples,
            )

            timeout = min(measurement_service.context.time_remaining, 10.0)
            voltage_values = task.read(number_of_samples, timeout)
            task = None  # Don't abort after this point

    _log_measured_values(voltage_values)
    logging.info("Completed measurement")
    return (voltage_values,)


def _log_measured_values(samples: list[float], max_samples_to_display: int = 5) -> None:
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

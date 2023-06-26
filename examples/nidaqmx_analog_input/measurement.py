"""Perform a finite analog input measurement with NI-DAQmx."""

import logging
import pathlib
from typing import Optional

import click
import nidaqmx
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_grpc_device_channel,
    get_service_options,
    grpc_device_options,
    verbosity_option,
)
from _nidaqmx_helpers import create_task
from nidaqmx.constants import TaskMode

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDAQmxAnalogInput.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIDAQmxAnalogInput.measui"],
)
service_options = ServiceOptions()

# If another measurement is using the session, the reserve function will wait
# for it to complete. Specify a reservation timeout to aid in debugging missed
# unreserve calls. Long measurements may require a longer timeout.
RESERVATION_TIMEOUT_IN_SECONDS = 60.0


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_name",
    nims.DataType.Pin,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DAQMX,
)
@measurement_service.configuration("sample_rate", nims.DataType.Double, 1000.0)
@measurement_service.configuration("number_of_samples", nims.DataType.UInt64, 100)
@measurement_service.output("acquired_samples", nims.DataType.DoubleArray1D)
def measure(pin_name, sample_rate, number_of_samples):
    """Perform a finite analog input measurement with NI-DAQmx."""
    logging.info(
        "Executing measurement: pin_name=%s sample_rate=%g number_of_samples=%d",
        pin_name,
        sample_rate,
        number_of_samples,
    )
    session_management_client = create_session_management_client(measurement_service)
    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=[pin_name],
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DAQMX,
        timeout=RESERVATION_TIMEOUT_IN_SECONDS,
    ) as reservation:
        task: Optional[nidaqmx.Task] = None

        def cancel_callback():
            logging.info("Canceling measurement")
            task_to_abort = task
            if task_to_abort is not None:
                task_to_abort.control(TaskMode.TASK_ABORT)

        measurement_service.context.add_cancel_callback(cancel_callback)

        grpc_device_channel = get_grpc_device_channel(measurement_service, nidaqmx, service_options)
        with create_task(reservation.session_info, grpc_device_channel) as task:
            if not reservation.session_info.session_exists:
                task.ai_channels.add_ai_voltage_chan(reservation.session_info.channel_list)

            task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                samps_per_chan=number_of_samples,
            )

            timeout = min(measurement_service.context.time_remaining, 10.0)
            voltage_values = task.read(
                number_of_samples_per_channel=number_of_samples, timeout=timeout
            )
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
@grpc_device_options
def main(verbosity: int, **kwargs):
    """Perform a finite analog input measurement with NI-DAQmx."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

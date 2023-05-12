"""Perform a finite analog input measurement with NI-DAQmx."""

import contextlib
import logging
import pathlib
from typing import Optional

import click
import grpc
import nidaqmx
from _helpers import (
    ServiceOptions,
    configure_logging,
    get_service_options,
    grpc_device_options,
    verbosity_option,
)
from nidaqmx.constants import TaskMode

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDAQmxAnalogInput.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIDAQmxAnalogInput.measui"],
)
service_options = ServiceOptions()


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
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DAQMX,
                # If another measurement is using the session, wait for it to complete.
                # Specify a timeout to aid in debugging missed unreserve calls.
                # Long measurements may require a longer timeout.
                timeout=60,
            )
        )
        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )
        session_info = reservation.session_info[0]
        task: Optional[nidaqmx.Task] = None

        def cancel_callback():
            logging.info("Canceling measurement")
            task_to_abort = task
            if task_to_abort is not None:
                task_to_abort.control(TaskMode.TASK_ABORT)

        measurement_service.context.add_cancel_callback(cancel_callback)

        task = stack.enter_context(_create_nidaqmx_task(session_info))
        if not session_info.session_exists:
            task.ai_channels.add_ai_voltage_chan(session_info.channel_list)

        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            samps_per_chan=number_of_samples,
        )

        timeout = min(measurement_service.context.time_remaining, 10.0)
        voltage_values = task.read(number_of_samples_per_channel=number_of_samples, timeout=timeout)
        task = None  # Don't abort after this point

    _log_measured_values(voltage_values)
    logging.info("Completed measurement")
    return (voltage_values,)


def _create_nidaqmx_task(
    session_info: nims.session_management.SessionInformation,
) -> nidaqmx.Task:
    session_kwargs = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=nidaqmx.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["grpc_options"] = nidaqmx.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=nidaqmx.SessionInitializationBehavior.AUTO,
        )

    return nidaqmx.Task(new_task_name=session_info.session_name, **session_kwargs)


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

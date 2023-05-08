"""Perform a finite analog input measurement with NI-DAQmx."""

import contextlib
import logging
import pathlib
import sys

import click
import grpc
import nidaqmx
from _helpers import ServiceOptions
from nidaqmx.grpc_session_options import (
    GrpcSessionOptions,
    GRPC_SERVICE_INTERFACE_NAME,
    SessionInitializationBehavior,
)

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
def measure(physical_channel, sample_rate, number_of_samples):
    """Perform a finite analog input measurement with NI-DAQmx."""
    logging.info(
        "Executing measurement: physical_channel=%s sample_rate=%g number_of_samples=%d",
        physical_channel,
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
                pin_or_relay_names=[physical_channel],
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
        task = stack.enter_context(_create_nidaqmx_task(session_info))
        channel_mappings = session_info.channel_mappings
        pending_cancellation = False

        def cancel_callback():
            logging.info("Canceling measurement")
            session_to_abort = task
            task_to_abort = task
            if task_to_abort is not None:
                nonlocal pending_cancellation
                pending_cancellation = True
                session_to_abort.abort()

        measurement_service.context.add_cancel_callback(cancel_callback)
        time_remaining = measurement_service.context.time_remaining

        timeout = min(time_remaining, 10.0)
        channel = next(
            channel_mapping.channel
            for channel_mapping in channel_mappings
            if channel_mapping.pin_or_relay_name == physical_channel
        )
        task.ai_channels.add_ai_voltage_chan(channel, min_val=0, max_val=5)
        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            samps_per_chan=number_of_samples,
        )
        voltage_values = task.read(
            number_of_samples_per_channel=number_of_samples, timeout=timeout
        )
        task = None  # Don't abort after this point

    _log_measured_values(voltage_values)
    logging.info("Completed measurement")
    return (voltage_values,)


def _create_nidaqmx_task(
    session_info: nims.session_management.SessionInformation,
) -> nidaqmx.Task:
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        grpc_session_options = GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=SessionInitializationBehavior.AUTO,
        )

    return nidaqmx.Task(
        new_task_name=session_info.resource_name, grpc_options=grpc_session_options
    )


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
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
@click.option(
    "--use-grpc-device/--no-use-grpc-device",
    default=True,
    is_flag=True,
    help="Use the NI gRPC Device Server.",
)
@click.option(
    "--grpc-device-address",
    default="",
    help="NI gRPC Device Server address (e.g. localhost:31763). If unspecified, use the discovery service to resolve the address.",
)
def main(verbose: int, use_grpc_device: bool, grpc_device_address: str):
    """Perform a finite analog input measurement with NI-DAQmx."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)
    global service_options
    service_options = ServiceOptions(
        use_grpc_device=use_grpc_device, grpc_device_address=grpc_device_address
    )
    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    sys.exit(main())

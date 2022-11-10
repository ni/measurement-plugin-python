"""User Measurement.

User can Import driver and 3rd Party Packages based on requirements.

"""

import contextlib
import logging
import pathlib
import sys
import time
from typing import List, NamedTuple

import click
import grpc
import hightime
import nidcpower

import ni_measurement_service as nims


NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059

measurement_info = nims.MeasurementInfo(
    display_name="DCMeasurement(Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "DCMeasurement.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.DCMeasurement_Python",
    description_url="https://www.ni.com/measurementservices/dcmeasurement.html",
)

dc_measurement_service = nims.MeasurementService(measurement_info, service_info)


class ServiceOptions(NamedTuple):
    """Service options specified on the command line."""

    use_grpc_device: bool
    grpc_device_address: str


service_options = ServiceOptions(use_grpc_device=False, grpc_device_address="")


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
    logging.info(
        "Executing measurement: resource_name=%s voltage_level=%g", resource_name, voltage_level
    )

    with contextlib.ExitStack() as stack:
        session_kwargs = {}
        if service_options.use_grpc_device:
            session_grpc_address = service_options.grpc_device_address
            if not session_grpc_address:
                session_grpc_address = dc_measurement_service.discovery_client.resolve_service(
                    provided_interface=nidcpower.GRPC_SERVICE_INTERFACE_NAME
                ).insecure_address
            session_grpc_channel = stack.enter_context(grpc.insecure_channel(session_grpc_address))
            session_kwargs["_grpc_options"] = nidcpower.GrpcSessionOptions(
                session_grpc_channel,
                session_name=resource_name,
                initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
            )

        session = stack.enter_context(
            nidcpower.Session(resource_name=resource_name, **session_kwargs)
        )

        pending_cancellation = False

        def cancel_callback():
            logging.info("Canceling measurement")
            session_to_abort = session
            if session_to_abort is not None:
                nonlocal pending_cancellation
                pending_cancellation = True
                session_to_abort.abort()

        dc_measurement_service.context.add_cancel_callback(cancel_callback)
        time_remaining = dc_measurement_service.context.time_remaining

        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = voltage_level_range
        session.current_limit_range = current_limit_range
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.voltage_level = voltage_level
        measured_value: List[nidcpower.Measurement] = []
        in_compliance = False
        with session.initiate():
            deadline = time.time() + time_remaining
            while True:
                if time.time() > deadline:
                    dc_measurement_service.context.abort(
                        grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded"
                    )
                if pending_cancellation:
                    dc_measurement_service.context.abort(
                        grpc.StatusCode.CANCELLED, "client requested cancellation"
                    )
                try:
                    session.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE, timeout=0.1)
                    break
                except nidcpower.DriverError as e:
                    """
                    There is no native way to support cancellation when taking a DCPower
                    measurement. To support cancellation, we will be calling WaitForEvent
                    until it succeeds or we have gone past the specified timeout. WaitForEvent
                    will throw an exception if it times out, which is why we are catching
                    and doing nothing.
                    """
                    if e.code == NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE:
                        pass
                    else:
                        raise
            channel = session.get_channel_names("0")
            measured_value = session.channels[channel].measure_multiple()
            in_compliance = session.channels[channel].query_in_compliance()
        session = None  # Don't abort after this point

    _log_measured_values(measured_value, in_compliance)
    logging.info("Completed measurement")
    return (measured_value[0].voltage, measured_value[0].current)


def _log_measured_values(measured_value, in_compliance):
    """Log the measured values."""
    logging.info("Voltage: %g V", measured_value[0].voltage)
    logging.info("Current: %g A", measured_value[0].current)
    logging.info("In compliance: %s", str(in_compliance))


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
)
@click.option(
    "--use-grpc-device", default=False, is_flag=True, help="Use the NI gRPC Device Server."
)
@click.option(
    "--grpc-device-address",
    default="",
    help="NI gRPC Device Server address (e.g. localhost:31763). If unspecified, use the discovery service to resolve the address.",
)
def main(verbose: int, use_grpc_device: bool, grpc_device_address: str):
    """Host the DC Measurement (Screen UI) service."""
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

    with dc_measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    sys.exit(main())

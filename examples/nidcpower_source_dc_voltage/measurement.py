"""Source and measure a DC voltage with an NI SMU."""

import contextlib
import logging
import pathlib
import sys
import time
from typing import Iterable

import click
import grpc
import hightime
import nidcpower
from _helpers import ServiceOptions

import ni_measurementlink_service as nims


NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE = -1074116059
NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE = -1074097933

measurement_info = nims.MeasurementInfo(
    display_name="NI-DCPower Source DC Voltage (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NIDCPowerSourceDCVoltage.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NIDCPowerSourceDCVoltage_Python",
    description_url="",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)
service_options = ServiceOptions()


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.PinArray1D,
    ["Pin1"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
@measurement_service.configuration("voltage_level_range", nims.DataType.Double, 6.0)
@measurement_service.configuration("current_limit", nims.DataType.Double, 0.01)
@measurement_service.configuration("current_limit_range", nims.DataType.Double, 0.01)
@measurement_service.configuration("source_delay", nims.DataType.Double, 0.0)
@measurement_service.output("measurement_sites", nims.DataType.Int32Array1D)
@measurement_service.output("measurement_pin_names", nims.DataType.StringArray1D)
@measurement_service.output("voltage_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("current_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("in_compliance", nims.DataType.BooleanArray1D)
def measure(
    pin_names: Iterable[str],
    voltage_level: float,
    voltage_level_range: float,
    current_limit: float,
    current_limit_range: float,
    source_delay: float,
):
    """Source and measure a DC voltage with an NI SMU."""
    logging.info("Executing measurement: pin_names=%s voltage_level=%g", pin_names, voltage_level)

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
                pin_or_relay_names=pin_names,
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
                timeout=-1,
            )
        )

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        session_info = reservation.session_info[0]
        session = stack.enter_context(_create_nidcpower_session(session_info))
        channels = session.channels[session_info.channel_list]
        channel_mappings = session_info.channel_mappings

        pending_cancellation = False

        def cancel_callback():
            logging.info("Canceling measurement")
            session_to_abort = session
            if session_to_abort is not None:
                nonlocal pending_cancellation
                pending_cancellation = True
                session_to_abort.abort()

        measurement_service.context.add_cancel_callback(cancel_callback)
        time_remaining = measurement_service.context.time_remaining

        channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
        channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        channels.current_limit = current_limit
        channels.voltage_level_range = voltage_level_range
        channels.current_limit_range = current_limit_range
        channels.source_delay = hightime.timedelta(seconds=source_delay)
        channels.voltage_level = voltage_level
        # The Measurement named tuple doesn't support type annotations:
        # https://github.com/ni/nimi-python/issues/1885
        measured_values = []
        with channels.initiate():
            deadline = time.time() + time_remaining
            while True:
                if time.time() > deadline:
                    measurement_service.context.abort(
                        grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded"
                    )
                if pending_cancellation:
                    measurement_service.context.abort(
                        grpc.StatusCode.CANCELLED, "client requested cancellation"
                    )
                try:
                    channels.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE, timeout=0.1)
                    break
                except nidcpower.Error as e:
                    """
                    There is no native way to support cancellation when taking a DCPower
                    measurement. To support cancellation, we will be calling WaitForEvent
                    until it succeeds or we have gone past the specified timeout. WaitForEvent
                    will throw an exception if it times out, which is why we are catching
                    and doing nothing.
                    """
                    if (
                        e.code == NIDCPOWER_WAIT_FOR_EVENT_TIMEOUT_ERROR_CODE
                        or e.code == NIDCPOWER_TIMEOUT_EXCEEDED_ERROR_CODE
                    ):
                        pass
                    else:
                        raise

            measured_values = channels.measure_multiple()
            for index, mapping in enumerate(channel_mappings):
                measured_values[index] = measured_values[index]._replace(
                    in_compliance=session.channels[mapping.channel].query_in_compliance()
                )
        session = None  # Don't abort after this point

    _log_measured_values(channel_mappings, measured_values)
    logging.info("Completed measurement")
    return (
        [m.site for m in channel_mappings],
        [m.pin_or_relay_name for m in channel_mappings],
        [m.voltage for m in measured_values],
        [m.current for m in measured_values],
        [m.in_compliance for m in measured_values],
    )


def _create_nidcpower_session(
    session_info: nims.session_management.SessionInformation,
) -> nidcpower.Session:
    session_kwargs = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=nidcpower.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["grpc_options"] = nidcpower.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=nidcpower.SessionInitializationBehavior.AUTO,
        )

    return nidcpower.Session(resource_name=session_info.resource_name, **session_kwargs)


def _log_measured_values(
    channel_mappings: Iterable[nims.session_management.ChannelMapping],
    measured_values: Iterable,
):
    """Log the measured values."""
    for mapping, measurement in zip(channel_mappings, measured_values):
        logging.info("site%s/%s:", mapping.site, mapping.pin_or_relay_name)
        logging.info("  Voltage: %g V", measurement.voltage)
        logging.info("  Current: %g A", measurement.current)
        logging.info("  In compliance: %s", str(measurement.in_compliance))


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
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
    """Source and measure a DC voltage with an NI SMU."""
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

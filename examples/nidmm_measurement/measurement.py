"""Perform a measurement using an NI DMM."""

import contextlib
import logging
import pathlib
import sys
from typing import Tuple

import click
import grpc
import nidmm
from _helpers import ServiceOptions, str_to_enum

import ni_measurement_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="NI-DMM Measurement (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NIDmmMeasurement.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NIDmmMeasurement_Python",
    description_url="https://www.ni.com/measurementservices/nidmmmeasurement.html",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)
service_options = ServiceOptions(use_grpc_device=False, grpc_device_address="")

FUNCTION_TO_ENUM = {
    "DC Volts": nidmm.Function.DC_VOLTS,
    "AC Volts": nidmm.Function.AC_VOLTS,
    "DC Current": nidmm.Function.DC_CURRENT,
    "AC Current": nidmm.Function.AC_CURRENT,
    "2-wire Resistance": nidmm.Function.TWO_WIRE_RES,
    "4-wire Resistance": nidmm.Function.FOUR_WIRE_RES,
    "Diode": nidmm.Function.DIODE,
    "Frequency": nidmm.Function.FREQ,
    "Period": nidmm.Function.PERIOD,
    "AC Volts DC Coupled": nidmm.Function.AC_VOLTS_DC_COUPLED,
    "Capacitance": nidmm.Function.CAPACITANCE,
    "Inductance": nidmm.Function.INDUCTANCE,
    "Temperature": nidmm.Function.TEMPERATURE,
}


@measurement_service.register_measurement
@measurement_service.configuration("pin_name", nims.DataType.Pin, "Pin1")
@measurement_service.configuration("measurement_type", nims.DataType.String, "DC Volts")
@measurement_service.configuration("range", nims.DataType.Double, 10.0)
@measurement_service.configuration("resolution_digits", nims.DataType.Double, 5.5)
@measurement_service.output("measured_value", nims.DataType.Double)
@measurement_service.output("signal_out_of_range", nims.DataType.Boolean)
@measurement_service.output("absolute_resolution", nims.DataType.Double)
def measure(
    pin_name: str,
    measurement_type: str,
    range: float,
    resolution_digits: str,
) -> Tuple:
    """Perform a measurement using an NI DMM."""
    logging.info(
        "Starting measurement: pin_name=%s measurement_type=%s range=%g resolution_digits=%g",
        pin_name,
        measurement_type,
        range,
        resolution_digits,
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
                pin_names=[pin_name],
                instrument_type_id="niDMM",
                timeout=-1,
            )
        )

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        session_info = reservation.session_info[0]
        session = stack.enter_context(_create_nidmm_session(session_info))
        session.configure_measurement_digits(
            str_to_enum(FUNCTION_TO_ENUM, measurement_type),
            range,
            resolution_digits,
        )
        measured_value = session.read()

        # TODO: https://github.com/ni/nimi-python/issues/1869
        # NI-DMM: IsOverRange and IsUnderRange are not supported
        signal_out_of_range = False

        absolute_resolution = session.resolution_absolute
        return (measured_value, signal_out_of_range, absolute_resolution)


def _create_nidmm_session(
    session_info: nims.session_management.SessionInformation,
) -> nidmm.Session:
    session_kwargs = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=nidmm.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["_grpc_options"] = nidmm.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.resource_name,
            initialization_behavior=nidmm.SessionInitializationBehavior.AUTO,
        )

    return nidmm.Session(session_info.resource_name, **session_kwargs)


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
@click.option(
    "--use-grpc-device",
    default=False,
    is_flag=True,
    help="Use the NI gRPC Device Server.",
)
@click.option(
    "--grpc-device-address",
    default="",
    help="NI gRPC Device Server address (e.g. localhost:31763). If unspecified, use the discovery service to resolve the address.",
)
def main(verbose: int, use_grpc_device: bool, grpc_device_address: str):
    """Perform a measurement using an NI DMM."""
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

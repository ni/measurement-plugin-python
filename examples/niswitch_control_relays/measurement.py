"""Control relays on NI switches."""

import contextlib
import logging
import pathlib
import sys
from typing import Tuple

import click
import niswitch
from _helpers import ServiceOptions

import ni_measurement_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="NI-SWITCH Control Relays (Py)",
    version="0.1.0.0",
    ui_file_paths=[pathlib.Path(__file__).resolve().parent / "NISwitchControlRelays.measui"],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.NISwitchControlRelays_Python",
    description_url="https://www.ni.com/measurementlink/examples/niswitchcontrolrelays.html",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)
service_options = ServiceOptions(use_grpc_device=False, grpc_device_address="")


@measurement_service.register_measurement
# TODO: Make relay_names PinArray1D
@measurement_service.configuration("relay_names", nims.DataType.Pin, "SiteRelay1")
@measurement_service.configuration("close_relay", nims.DataType.Boolean, True)
def measure(
    relay_names: str,
    close_relays: bool,
) -> Tuple:
    """Control relays on NI switches."""
    logging.info(
        "Controlling relays: relay_names=%s close_relay=%s",
        relay_names,
        close_relays,
    )

    session_management_client = nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )

    with contextlib.ExitStack() as stack:
        relay_list = [r.strip() for r in relay_names.split(",")]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_names=relay_list,
                instrument_type_id="niRelayDriver",
                timeout=-1,
            )
        )

        sessions = [
            stack.enter_context(_create_niswitch_session(session_info))
            for session_info in reservation.session_info
        ]

        for session, session_info in zip(sessions, reservation.session_info):
            session.relay_control(
                session_info.channel_list,
                niswitch.RelayAction.CLOSE if close_relays else niswitch.RelayAction.OPEN,
            )
        for session in sessions:
            session.wait_for_debounce()

    logging.info("Completed operation")
    return ()


def _create_niswitch_session(
    session_info: nims.session_management.SessionInformation,
) -> niswitch.Session:
    session_kwargs = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=niswitch.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["_grpc_options"] = niswitch.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.resource_name,
            initialization_behavior=niswitch.SessionInitializationBehavior.AUTO,
        )

    # This uses the topology configured in MAX.
    return niswitch.Session(session_info.resource_name, **session_kwargs)


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
    """Control relays on NI switches."""
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

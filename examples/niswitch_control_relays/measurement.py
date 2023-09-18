"""Control relays using an NI relay driver (e.g. PXI-2567)."""

import contextlib
import logging
import pathlib
import sys
from typing import Any, Tuple

import click
import niswitch
from _constants import USE_SIMULATION
from _helpers import (
    ServiceOptions,
    configure_logging,
    create_session_management_client,
    get_grpc_device_channel,
    get_service_options,
    grpc_device_options,
    use_simulation_option,
    verbosity_option,
)
from _niswitch_helpers import create_session

import ni_measurementlink_service as nims

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NISwitchControlRelays.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NISwitchControlRelays.measui"],
)
service_options = ServiceOptions()

RESERVATION_TIMEOUT_IN_SECONDS = 60.0
"""
If another measurement is using the session, the reserve function will wait
for it to complete. Specify a reservation timeout to aid in debugging missed
unreserve calls. Long measurements may require a longer timeout.
"""


@measurement_service.register_measurement
@measurement_service.configuration("relay_names", nims.DataType.String, "SiteRelay1")
@measurement_service.configuration("close_relay", nims.DataType.Boolean, True)
def measure(
    relay_names: str,
    close_relays: bool,
) -> Tuple[()]:
    """Control relays using an NI relay driver (e.g. PXI-2567)."""
    logging.info(
        "Controlling relays: relay_names=%s close_relay=%s",
        relay_names,
        close_relays,
    )

    session_management_client = create_session_management_client(measurement_service)

    with contextlib.ExitStack() as stack:
        relay_list = [r.strip() for r in relay_names.split(",")]
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_or_relay_names=relay_list,
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_RELAY_DRIVER,
                timeout=RESERVATION_TIMEOUT_IN_SECONDS,
            )
        )

        grpc_device_channel = get_grpc_device_channel(
            measurement_service, niswitch, service_options
        )
        sessions = [
            stack.enter_context(create_session(session_info, grpc_device_channel))
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


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs: Any) -> None:
    """Control relays using an NI relay driver (e.g. PXI-2567)."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

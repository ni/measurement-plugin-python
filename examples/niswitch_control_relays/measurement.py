"""Control relays using an NI relay driver (e.g. PXI-2567)."""

import logging
import pathlib
import sys

import click
import ni_measurement_plugin_sdk_service as nims
from _helpers import configure_logging, verbosity_option
from niswitch.enums import RelayAction

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NISwitchControlRelays.serviceconfig",
    ui_file_paths=[service_directory / "NISwitchControlRelays.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration("relay_names", nims.DataType.String, "SiteRelay1")
@measurement_service.configuration("close_relay", nims.DataType.Boolean, True)
def measure(
    relay_names: str,
    close_relays: bool,
) -> tuple[()]:
    """Control relays using an NI relay driver (e.g. PXI-2567)."""
    logging.info(
        "Controlling relays: relay_names=%s close_relay=%s",
        relay_names,
        close_relays,
    )

    with measurement_service.context.reserve_sessions(relay_names) as reservation:
        with reservation.initialize_niswitch_sessions() as session_infos:
            # Open or close all relays corresponding to the selected pins and
            # sites.
            for session_info in session_infos:
                session_info.session.relay_control(
                    session_info.channel_list,
                    RelayAction.CLOSE if close_relays else RelayAction.OPEN,
                )

            # Wait for all of the relays to activate and debounce.
            for session_info in session_infos:
                session_info.session.wait_for_debounce()

    logging.info("Completed operation")
    return ()


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Control relays using an NI relay driver (e.g. PXI-2567)."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

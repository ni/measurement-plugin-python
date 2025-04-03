"""Test a SPI device using an NI Digital Pattern instrument."""

from __future__ import annotations

import logging
import pathlib
import sys
from collections.abc import Iterable

import click
import ni_measurement_plugin_sdk_service as nims
import nidigital
from _helpers import configure_logging, verbosity_option

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDigitalSPI.serviceconfig",
    ui_file_paths=[service_directory / "NIDigitalSPI.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.IOResourceArray1D,
    ["SPI_PINS"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
)
@measurement_service.configuration(
    "specification_file_path", nims.DataType.Path, "Specifications.specs"
)
@measurement_service.configuration("levels_file_path", nims.DataType.Path, "PinLevels.digilevels")
@measurement_service.configuration("timing_file_path", nims.DataType.Path, "Timing.digitiming")
@measurement_service.configuration("pattern_file_path", nims.DataType.Path, "Pattern.digipat")
@measurement_service.configuration("load_files", nims.DataType.Boolean, True)
# TODO: Measurement Plug-In UI Editor doesn't support arrays of Booleans
@measurement_service.output("passing_sites", nims.DataType.Int32Array1D)
@measurement_service.output("failing_sites", nims.DataType.Int32Array1D)
def measure(
    pin_names: Iterable[str],
    specifications_file_path: str,
    levels_file_path: str,
    timing_file_path: str,
    pattern_file_path: str,
    load_files: bool,
) -> tuple:
    """Test a SPI device using an NI Digital Pattern instrument."""
    logging.info("Starting test: pin_names=%s", pin_names)

    with measurement_service.context.reserve_session(pin_names) as reservation:
        with reservation.initialize_nidigital_session() as session_info:
            session = session_info.session
            pin_map_context = measurement_service.context.pin_map_context
            selected_sites_string = ",".join(f"site{i}" for i in pin_map_context.sites or [])
            selected_sites = session.sites[selected_sites_string]

            if load_files:
                # When running the measurement from TestStand, teststand_fixture.py should have
                # already loaded the pin map, specifications, levels, timing, and patterns.
                session.load_pin_map(pin_map_context.pin_map_id)
                session.load_specifications_levels_and_timing(
                    str(_resolve_relative_path(service_directory, specifications_file_path)),
                    str(_resolve_relative_path(service_directory, levels_file_path)),
                    str(_resolve_relative_path(service_directory, timing_file_path)),
                )
                session.load_pattern(
                    str(_resolve_relative_path(service_directory, pattern_file_path)),
                )

            levels_file_name = pathlib.Path(levels_file_path).stem
            timing_file_name = pathlib.Path(timing_file_path).stem
            selected_sites.apply_levels_and_timing(levels_file_name, timing_file_name)
            selected_sites.burst_pattern(start_label="SPI_Pattern")
            site_pass_fail = selected_sites.get_site_pass_fail()
            passing_sites = [site for site, pass_fail in site_pass_fail.items() if pass_fail]
            failing_sites = [site for site, pass_fail in site_pass_fail.items() if not pass_fail]
            session.selected_function = nidigital.SelectedFunction.DISCONNECT

    logging.info("Completed test: passing_sites=%s failing_sites=%s", passing_sites, failing_sites)
    return (passing_sites, failing_sites)


def _resolve_relative_path(
    directory_path: pathlib.Path, file_path: str | pathlib.Path
) -> pathlib.Path:
    file_path = pathlib.Path(file_path)
    if file_path.is_absolute():
        return file_path
    else:
        return (directory_path / file_path).resolve()


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Test a SPI device using an NI Digital Pattern instrument."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

"""Test a SPI device using an NI Digital Pattern instrument."""

import logging
import pathlib
from typing import Iterable, Tuple, Union

import click
import grpc
import nidigital
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
from _nidigital_helpers import USE_SIMULATION, create_session

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDigitalSPI.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIDigitalSPI.measui"],
)
service_options = ServiceOptions()


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.PinArray1D,
    ["SPI_PINS"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
)
@measurement_service.configuration(
    "specification_file_path", nims.DataType.Path, "Specifications.specs"
)
@measurement_service.configuration("levels_file_path", nims.DataType.Path, "PinLevels.digilevels")
@measurement_service.configuration("timing_file_path", nims.DataType.Path, "Timing.digitiming")
@measurement_service.configuration("pattern_file_path", nims.DataType.Path, "Pattern.digipat")
# TODO: MeasurementLink UI Editor doesn't support arrays of Booleans
@measurement_service.output("passing_sites", nims.DataType.Int32Array1D)
@measurement_service.output("failing_sites", nims.DataType.Int32Array1D)
def measure(
    pin_names: Iterable[str],
    specifications_file_path: str,
    levels_file_path: str,
    timing_file_path: str,
    pattern_file_path: str,
) -> Tuple:
    """Test a SPI device using an NI Digital Pattern instrument."""
    logging.info("Starting test: pin_names=%s", pin_names)

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_sessions(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
        # If another measurement is using the session, wait for it to complete.
        # Specify a timeout to aid in debugging missed unreserve calls.
        # Long measurements may require a longer timeout.
        timeout=60,
    ) as reservation:
        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        session_info = reservation.session_info[0]
        grpc_device_channel = get_grpc_device_channel(measurement_service, nidigital)
        with create_session(session_info, grpc_device_channel) as session:
            pin_map_context = measurement_service.context.pin_map_context
            selected_sites_string = ",".join(f"site{i}" for i in pin_map_context.sites)
            selected_sites = session.sites[selected_sites_string]

            if not session_info.session_exists:
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

            selected_sites.apply_levels_and_timing(
                str(_resolve_relative_path(service_directory, levels_file_path)),
                str(_resolve_relative_path(service_directory, timing_file_path)),
            )
            selected_sites.burst_pattern(start_label="SPI_Pattern")
            site_pass_fail = selected_sites.get_site_pass_fail()
            passing_sites = [site for site, pass_fail in site_pass_fail.items() if pass_fail]
            failing_sites = [site for site, pass_fail in site_pass_fail.items() if not pass_fail]
            session.selected_function = nidigital.SelectedFunction.DISCONNECT

    logging.info("Completed test: passing_sites=%s failing_sites=%s", passing_sites, failing_sites)
    return (passing_sites, failing_sites)


def _resolve_relative_path(
    directory_path: pathlib.Path, file_path: Union[str, pathlib.Path]
) -> pathlib.Path:
    if not isinstance(file_path, pathlib.Path):
        file_path = pathlib.Path(file_path)
    if file_path.is_absolute():
        return file_path
    else:
        return (directory_path / file_path).resolve()


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Test a SPI device using an NI Digital Pattern instrument."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

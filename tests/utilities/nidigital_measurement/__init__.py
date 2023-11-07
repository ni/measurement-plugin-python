"""NI-Digital MeasurementLink test service."""
import pathlib
from typing import Iterable, Sequence, Tuple, Union

import nidigital

import ni_measurementlink_service as nims
from ni_measurementlink_service.session_management import TypedSessionInformation

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDigitalMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.StringArray1D, ["CS"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
@measurement_service.output("passing_sites", nims.DataType.Int32Array1D)
@measurement_service.output("failing_sites", nims.DataType.Int32Array1D)
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> Tuple[
    Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[str]
]:
    """NI-Digital MeasurementLink test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nidigital_sessions() as session_infos:
                connections = reservation.get_nidigital_connections(pin_names)
                assert all([session_info is not None for session_info in session_infos])
                passing_sites, failing_sites = _burst_spi_pattern(session_infos)
                site0_connections, site1_connections = [], []
                # Assumption: All pins connected to site0 belongs to one session and
                # all the pins connected to site1 belongs to the other session.
                for connection in connections:
                    if connection.channel_name.startswith("site0"):
                        site0_connections.append(connection.channel_name)
                    elif connection.channel_name.startswith("site1"):
                        site1_connections.append(connection.channel_name)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [", ".join(site0_connections), ", ".join(site1_connections)],
                    list(passing_sites),
                    list(failing_sites),
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nidigital_session() as session_info:
                connection = reservation.get_nidigital_connection(list(pin_names)[0])
                assert session_info is not None
                passing_sites, failing_sites = _burst_spi_pattern([session_info])

                return (
                    [session_info.session_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                    passing_sites,
                    failing_sites,
                )


def _burst_spi_pattern(
    session_infos: Sequence[TypedSessionInformation[nidigital.Session]],
) -> Tuple:
    specifications_file_path = "Specifications.specs"
    levels_file_path = "PinLevels.digilevels"
    timing_file_path = "Timing.digitiming"
    pattern_file_path = "Pattern.digipat"
    pin_map_context = measurement_service.context.pin_map_context
    selected_sites_string = ",".join(f"site{i}" for i in pin_map_context.sites or [])

    passing_sites_list, failing_sites_list = [], []
    for session_info in session_infos:
        session = session_info.session
        selected_sites = session.sites[selected_sites_string]

        if not session_info.session_exists:
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

    for session_info in session_infos:
        selected_sites = session_info.session.sites[selected_sites_string]
        selected_sites.apply_levels_and_timing(levels_file_name, timing_file_name)

    for session_info in session_infos:
        selected_sites = session_info.session.sites[selected_sites_string]
        selected_sites.burst_pattern(start_label="SPI_Pattern", wait_until_done=False)

    for session_info in session_infos:
        selected_sites = session_info.session.sites[selected_sites_string]
        session_info.session.wait_until_done()
        site_pass_fail = selected_sites.get_site_pass_fail()
        passing_sites = [site for site, pass_fail in site_pass_fail.items() if pass_fail]
        failing_sites = [site for site, pass_fail in site_pass_fail.items() if not pass_fail]
        passing_sites_list.extend(passing_sites)
        failing_sites_list.extend(failing_sites)
        session.selected_function = nidigital.SelectedFunction.DISCONNECT

    return (passing_sites_list, failing_sites_list)


def _resolve_relative_path(
    directory_path: pathlib.Path, file_path: Union[str, pathlib.Path]
) -> pathlib.Path:
    file_path = pathlib.Path(file_path)
    if file_path.is_absolute():
        return file_path
    else:
        return (directory_path / file_path).resolve()

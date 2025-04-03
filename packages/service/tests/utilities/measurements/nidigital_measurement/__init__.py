"""NI-Digital measurement plug-in test service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Sequence
from itertools import groupby
from typing import Tuple

import nidigital

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service.session_management import (
    TypedConnection,
    TypedSessionInformation,
)

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDigitalMeasurement.serviceconfig",
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
) -> tuple[
    Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[int], Iterable[int]
]:
    """NI-Digital measurement plug-in test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nidigital_sessions() as session_infos:
                connections = reservation.get_nidigital_connections(pin_names)
                assert all([session_info.session is not None for session_info in session_infos])
                passing_sites, failing_sites = _burst_spi_pattern(session_infos)
                connections_by_session = [
                    list(g) for _, g in groupby(sorted(connections, key=_key_func), key=_key_func)
                ]

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [
                        ", ".join(conn.channel_name for conn in conns)
                        for conns in connections_by_session
                    ],
                    passing_sites,
                    failing_sites,
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nidigital_session() as session_info:
                connection = reservation.get_nidigital_connection(list(pin_names)[0])
                assert session_info.session is not None
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
) -> tuple[list[int], list[int]]:
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
    directory_path: pathlib.Path, file_path: str | pathlib.Path
) -> pathlib.Path:
    file_path = pathlib.Path(file_path)
    if file_path.is_absolute():
        return file_path
    else:
        return (directory_path / file_path).resolve()


def _key_func(conn: TypedConnection[nidigital.Session]) -> str:
    return conn.session_info.session_name

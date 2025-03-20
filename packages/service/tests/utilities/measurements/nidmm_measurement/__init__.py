"""NI-DMM measurement plug-in test service."""

from __future__ import annotations

import math
import pathlib
from collections.abc import Iterable, Sequence
from typing import List

import nidmm

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service.session_management import TypedSessionInformation

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDmmMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.IOResourceArray1D, ["Pin1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
@measurement_service.output("signals_out_of_range", nims.DataType.BooleanArray1D)
@measurement_service.output("absolute_resolutions", nims.DataType.DoubleArray1D)
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> tuple[list[str], list[str], list[str], list[str], list[bool], list[float]]:
    """NI-DMM measurement plug-in test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nidmm_sessions() as session_infos:
                connections = reservation.get_nidmm_connections(pin_names)
                assert all([session_info.session is not None for session_info in session_infos])
                signals_out_of_range, absolute_resolutions = _get_dmm_readings(session_infos)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                    signals_out_of_range,
                    absolute_resolutions,
                )

    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nidmm_session() as session_info:
                connection = reservation.get_nidmm_connection(list(pin_names)[0])
                assert session_info.session is not None
                signals_out_of_range, absolute_resolutions = _get_dmm_readings([session_info])

                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                    signals_out_of_range,
                    absolute_resolutions,
                )


def _get_dmm_readings(
    session_infos: Sequence[TypedSessionInformation[nidmm.Session]],
) -> tuple[list[bool], list[float]]:
    nidmm_function = nidmm.Function(nidmm.Function.DC_VOLTS.value)
    range = 10.0
    resolution_digits = 5.5

    signals_out_of_range, absolute_resolutions = [], []
    for session_info in session_infos:
        session_info.session.configure_measurement_digits(nidmm_function, range, resolution_digits)

    for session_info in session_infos:
        session = session_info.session
        measured_value = session.read()
        signal_out_of_range = math.isnan(measured_value) or math.isinf(measured_value)
        absolute_resolution = session.resolution_absolute
        signals_out_of_range.append(signal_out_of_range)
        absolute_resolutions.append(absolute_resolution)

    return (signals_out_of_range, absolute_resolutions)

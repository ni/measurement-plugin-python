"""Pin-aware measurement plug-in test service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable
from typing import Tuple

import ni_measurement_plugin_sdk_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "PinAwareMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.IOResourceArray1D, ["Pin1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("pin_map_id", nims.DataType.String)
@measurement_service.output("sites", nims.DataType.Int32Array1D)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> tuple[str, Iterable[int], Iterable[str], Iterable[str], Iterable[str]]:
    """Pin-aware measurement plug-in test service."""
    pin_map_context = measurement_service.context.pin_map_context
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            return (
                pin_map_context.pin_map_id,
                pin_map_context.sites or [],
                [s.session_name for s in reservation.session_info],
                [s.resource_name for s in reservation.session_info],
                [s.channel_list for s in reservation.session_info],
            )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            return (
                pin_map_context.pin_map_id,
                pin_map_context.sites or [],
                [reservation.session_info.resource_name],
                [reservation.session_info.resource_name],
                [reservation.session_info.channel_list],
            )

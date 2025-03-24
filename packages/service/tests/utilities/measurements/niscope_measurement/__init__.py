"""NI-SCOPE measurement plug-in test service."""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Sequence
from contextlib import ExitStack
from typing import List

import niscope

import ni_measurement_plugin_sdk_service as nims
from ni_measurement_plugin_sdk_service.session_management import TypedSessionInformation

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIScopeMeasurement.serviceconfig",
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
@measurement_service.output("waveform", nims.DataType.DoubleArray1D)
def measure(
    pin_names: Iterable[str], multi_session: bool
) -> tuple[Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[float]]:
    """NI-SCOPE measurement plug-in test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_niscope_sessions() as session_infos:
                assert all([session_info.session is not None for session_info in session_infos])
                connections = reservation.get_niscope_connections(pin_names)
                waveforms = _acquire_waveforms(session_infos)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                    waveforms[0],
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_niscope_session() as session_info:
                assert session_info.session is not None
                connection = reservation.get_niscope_connection(list(pin_names)[0])
                waveforms = _acquire_waveforms([session_info])

                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                    waveforms[0],
                )


def _acquire_waveforms(
    session_infos: Sequence[TypedSessionInformation[niscope.Session]],
) -> list[list[float]]:
    for session_info in session_infos:
        channel_order = session_info.channel_list
        trigger_channel = session_info.channel_list.split(",")[0]

        session_info.session.channels[channel_order].configure_vertical(
            5.0, niscope.VerticalCoupling.DC, enabled=True
        )
        session_info.session.channels[channel_order].configure_chan_characteristics(
            1e6, max_input_frequency=0.0
        )
        session_info.session.configure_horizontal_timing(
            10e6,
            5,
            ref_position=50.0,
            num_records=1,
            enforce_realtime=True,
        )
        session_info.session.configure_trigger_edge(
            trigger_channel,
            0.5,
            niscope.TriggerCoupling.DC,
            niscope.TriggerSlope.POSITIVE,
        )
        session_info.session.trigger_modifier = niscope.TriggerModifier.NO_TRIGGER_MOD

    waveforms = []
    with ExitStack() as stack:
        for session_info in session_infos:
            stack.enter_context(session_info.session.initiate())

        for session_info in session_infos:
            waveform_infos = session_info.session.channels[channel_order].fetch()
            for w in waveform_infos:
                waveforms.append(w.samples)

    return waveforms

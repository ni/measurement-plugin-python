"""Acquire a waveform using an NI oscilloscope."""

import logging
import pathlib
import sys
import time
from typing import List, Tuple

import click
import grpc
import niscope
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
from _niscope_helpers import create_session

import ni_measurementlink_service as nims

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIScopeAcquireWaveform.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIScopeAcquireWaveform.measui"],
)
service_options = ServiceOptions()

RESERVATION_TIMEOUT_IN_SECONDS = 60.0
"""
If another measurement is using the session, the reserve function will wait
for it to complete. Specify a reservation timeout to aid in debugging missed
unreserve calls. Long measurements may require a longer timeout.
"""


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.PinArray1D,
    ["Pin1", "Pin2", "Pin3", "Pin4"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_SCOPE,
)
@measurement_service.configuration("vertical_range", nims.DataType.Double, 5.0)
@measurement_service.configuration(
    "vertical_coupling",
    nims.DataType.Enum,
    niscope.VerticalCoupling.DC,
    enum_type=niscope.VerticalCoupling,
)
@measurement_service.configuration("input_impedance", nims.DataType.Double, 1e6)
@measurement_service.configuration("min_sample_rate", nims.DataType.Double, 10e6)
@measurement_service.configuration("min_record_length", nims.DataType.Int32, 40000)
@measurement_service.configuration(
    "trigger_source",
    nims.DataType.Pin,
    "Pin1",
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_SCOPE,
)
@measurement_service.configuration("trigger_level", nims.DataType.Double, 0.5)
@measurement_service.configuration(
    "trigger_slope",
    nims.DataType.Enum,
    niscope.TriggerSlope.POSITIVE,
    enum_type=niscope.TriggerSlope,
)
@measurement_service.configuration("auto_trigger", nims.DataType.Boolean, False)
@measurement_service.configuration(
    "trigger_coupling",
    nims.DataType.Enum,
    niscope.TriggerCoupling.DC,
    enum_type=niscope.TriggerCoupling,
)
@measurement_service.configuration("timeout", nims.DataType.Double, 5.0)
@measurement_service.output("waveform0", nims.DataType.DoubleArray1D)
@measurement_service.output("waveform1", nims.DataType.DoubleArray1D)
@measurement_service.output("waveform2", nims.DataType.DoubleArray1D)
@measurement_service.output("waveform3", nims.DataType.DoubleArray1D)
def measure(
    pin_names: str,
    vertical_range: float,
    vertical_coupling: str,
    input_impedance: float,
    min_sample_rate: float,
    min_record_length: int,
    trigger_source: str,
    trigger_level: float,
    trigger_slope: str,
    auto_trigger: bool,
    trigger_coupling: str,
    timeout: float,
) -> Tuple[List[float], ...]:
    """Acquire a waveform using an NI oscilloscope."""
    logging.info(
        "Starting acquisition: pin_or_relay_names=%s vertical_range=%g trigger_source=%s trigger_level=%g",
        pin_names,
        vertical_range,
        trigger_source,
        trigger_level,
    )

    pending_cancellation = False

    def cancel_callback() -> None:
        logging.info("Canceling acquisition")
        nonlocal pending_cancellation
        pending_cancellation = True

    measurement_service.context.add_cancel_callback(cancel_callback)

    session_management_client = create_session_management_client(measurement_service)

    with session_management_client.reserve_session(
        context=measurement_service.context.pin_map_context,
        pin_or_relay_names=pin_names,
        instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_SCOPE,
        timeout=RESERVATION_TIMEOUT_IN_SECONDS,
    ) as reservation:
        channel_names = reservation.session_info.channel_list
        pin_to_channel = {
            mapping.pin_or_relay_name: mapping.channel
            for mapping in reservation.session_info.channel_mappings
        }
        if trigger_source in pin_to_channel:
            trigger_source = pin_to_channel[trigger_source]

        grpc_device_channel = get_grpc_device_channel(measurement_service, niscope, service_options)
        with create_session(reservation.session_info, grpc_device_channel) as session:
            session.channels[""].channel_enabled = False
            session.channels[channel_names].configure_vertical(
                vertical_range,
                vertical_coupling,
            )
            session.channels[channel_names].configure_chan_characteristics(
                input_impedance, max_input_frequency=0.0
            )
            session.configure_horizontal_timing(
                min_sample_rate,
                min_record_length,
                ref_position=50.0,
                num_records=1,
                enforce_realtime=True,
            )
            session.configure_trigger_edge(
                trigger_source,
                trigger_level,
                trigger_coupling,
                trigger_slope,
            )
            session.trigger_modifier = (
                niscope.TriggerModifier.AUTO
                if auto_trigger
                else niscope.TriggerModifier.NO_TRIGGER_MOD
            )

            with session.initiate():
                deadline = time.time() + min(measurement_service.context.time_remaining, timeout)
                while True:
                    if time.time() > deadline:
                        measurement_service.context.abort(
                            grpc.StatusCode.DEADLINE_EXCEEDED, "Deadline exceeded."
                        )
                    if pending_cancellation:
                        measurement_service.context.abort(
                            grpc.StatusCode.CANCELLED, "Client requested cancellation."
                        )
                    status = session.acquisition_status()
                    if status == niscope.AcquisitionStatus.COMPLETE:
                        break
                    remaining_time = max(deadline - time.time(), 0.0)
                    sleep_time = min(remaining_time, 10e-3)
                    time.sleep(sleep_time)

                waveform_infos = session.channels[channel_names].fetch()
                return tuple(w.samples for w in waveform_infos)

    return ()


@click.command
@verbosity_option
@grpc_device_options
@use_simulation_option(default=USE_SIMULATION)
def main(verbosity: int, **kwargs) -> None:
    """Acquire a waveform using an NI oscilloscope."""
    configure_logging(verbosity)
    global service_options
    service_options = get_service_options(**kwargs)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

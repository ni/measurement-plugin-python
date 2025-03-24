"""Acquire a waveform using an NI oscilloscope."""

import logging
import pathlib
import sys
import threading
import time
from collections.abc import Sequence

import click
import grpc
import ni_measurement_plugin_sdk_service as nims
import niscope
from _helpers import configure_logging, verbosity_option

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIScopeAcquireWaveform.serviceconfig",
    ui_file_paths=[service_directory / "NIScopeAcquireWaveform.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration(
    "measurement_pins",
    nims.DataType.IOResourceArray1D,
    ["PinGroup1"],
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
    "trigger_pin",
    nims.DataType.IOResource,
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
    measurement_pins: Sequence[str],
    vertical_range: float,
    vertical_coupling: str,
    input_impedance: float,
    min_sample_rate: float,
    min_record_length: int,
    trigger_pin: str,
    trigger_level: float,
    trigger_slope: str,
    auto_trigger: bool,
    trigger_coupling: str,
    timeout: float,
) -> tuple[list[float], ...]:
    """Acquire a waveform using an NI oscilloscope."""
    logging.info(
        "Starting acquisition: measurement_pins=%s vertical_range=%g trigger_pin=%s trigger_level=%g",
        measurement_pins,
        vertical_range,
        trigger_pin,
        trigger_level,
    )

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    with measurement_service.context.reserve_session(
        list(measurement_pins) + [trigger_pin]
    ) as reservation:
        with reservation.initialize_niscope_session() as session_info:
            # Use connections to map pin names to channel names. This sets the
            # channel order based on the pin order and allows mapping the
            # resulting measurements back to the corresponding pins and sites.
            connections = reservation.get_niscope_connections(measurement_pins)
            channel_order = ",".join(connection.channel_name for connection in connections)
            trigger_connection = reservation.get_niscope_connection(trigger_pin)

            # Start with all channels in the session disabled. Some channels may
            # be connected to other pins or sites.
            session = session_info.session
            session.channels[""].channel_enabled = False

            # Enable and configure all channels corresponding to the selected
            # pins and site(s).
            session.channels[channel_order].configure_vertical(
                vertical_range, vertical_coupling, enabled=True
            )
            session.channels[channel_order].configure_chan_characteristics(
                input_impedance, max_input_frequency=0.0
            )

            # Configure timing and triggering for the acquisition.
            session.configure_horizontal_timing(
                min_sample_rate,
                min_record_length,
                ref_position=50.0,
                num_records=1,
                enforce_realtime=True,
            )
            session.configure_trigger_edge(
                trigger_connection.channel_name,
                trigger_level,
                trigger_coupling,
                trigger_slope,
            )
            session.trigger_modifier = (
                niscope.TriggerModifier.AUTO
                if auto_trigger
                else niscope.TriggerModifier.NO_TRIGGER_MOD
            )

            # Initiate the acquisition. initiate() returns a context manager
            # that aborts the measurement when the function returns or raises an
            # exception.
            with session.initiate():
                _wait_until_done(session, cancellation_event, timeout)
                waveform_infos = session.channels[channel_order].fetch()

    logging.info("Completed acquisition")
    return tuple(w.samples for w in waveform_infos)


def _wait_until_done(
    session: niscope.Session,
    cancellation_event: threading.Event,
    timeout: float,
) -> None:
    """Wait until the acquisition is done or error/cancellation occurs."""
    grpc_deadline = time.time() + measurement_service.context.time_remaining
    user_deadline = time.time() + timeout
    deadline = min(grpc_deadline, user_deadline)

    while True:
        if time.time() > user_deadline:
            raise TimeoutError("User timeout expired.")
        if time.time() > grpc_deadline:
            measurement_service.context.abort(
                grpc.StatusCode.DEADLINE_EXCEEDED, "Deadline exceeded."
            )
        if cancellation_event.is_set():
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

        status = session.acquisition_status()
        if status == niscope.AcquisitionStatus.COMPLETE:
            break

        remaining_time = max(deadline - time.time(), 0.0)
        sleep_time = min(remaining_time, 10e-3)
        time.sleep(sleep_time)


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Acquire a waveform using an NI oscilloscope."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()

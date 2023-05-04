"""Acquire a waveform using an NI oscilloscope."""

import contextlib
import logging
import pathlib
import time
from typing import Any, Dict, Tuple

import click
import grpc
import niscope
from _helpers import (
    ServiceOptions,
    configure_logging,
    get_service_options,
    grpc_device_options,
    str_to_enum,
    use_simulation_option,
    verbosity_option,
)

import ni_measurementlink_service as nims

# To use a physical NI oscilloscope instrument, set this to False or specify
# --no-use-simulation on the command line.
USE_SIMULATION = True

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIScopeAcquireWaveform.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "NIScopeAcquireWaveform.measui"],
)
service_options = ServiceOptions()

VERTICAL_COUPLING_TO_ENUM = {
    "AC": niscope.VerticalCoupling.AC,
    "DC": niscope.VerticalCoupling.DC,
    "GND": niscope.VerticalCoupling.GND,
}

TRIGGER_COUPLING_TO_ENUM = {
    "AC": niscope.TriggerCoupling.AC,
    "DC": niscope.TriggerCoupling.DC,
    "HF Reject": niscope.TriggerCoupling.HF_REJECT,
    "LF Reject": niscope.TriggerCoupling.LF_REJECT,
    "AC Plus HF Reject": niscope.TriggerCoupling.AC_PLUS_HF_REJECT,
}

TRIGGER_SLOPE_TO_ENUM = {
    "Positive": niscope.TriggerSlope.POSITIVE,
    "Negative": niscope.TriggerSlope.NEGATIVE,
}


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names",
    nims.DataType.PinArray1D,
    ["Pin1", "Pin2", "Pin3", "Pin4"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_SCOPE,
)
@measurement_service.configuration("vertical_range", nims.DataType.Double, 5.0)
@measurement_service.configuration("vertical_coupling", nims.DataType.String, "DC")
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
@measurement_service.configuration("trigger_slope", nims.DataType.String, "Positive")
@measurement_service.configuration("auto_trigger", nims.DataType.Boolean, False)
@measurement_service.configuration("trigger_coupling", nims.DataType.String, "DC")
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
) -> Tuple:
    """Acquire a waveform using an NI oscilloscope."""
    logging.info(
        "Starting acquisition: pin_or_relay_names=%s vertical_range=%g trigger_source=%s trigger_level=%g",
        pin_names,
        vertical_range,
        trigger_source,
        trigger_level,
    )

    pending_cancellation = False

    def cancel_callback():
        logging.info("Canceling acquisition")
        nonlocal pending_cancellation
        pending_cancellation = True

    measurement_service.context.add_cancel_callback(cancel_callback)

    session_management_client = nims.session_management.Client(
        grpc_channel=measurement_service.get_channel(
            provided_interface=nims.session_management.GRPC_SERVICE_INTERFACE_NAME,
            service_class=nims.session_management.GRPC_SERVICE_CLASS,
        )
    )

    with contextlib.ExitStack() as stack:
        reservation = stack.enter_context(
            session_management_client.reserve_sessions(
                context=measurement_service.context.pin_map_context,
                pin_or_relay_names=pin_names,
                instrument_type_id=nims.session_management.INSTRUMENT_TYPE_NI_SCOPE,
                # If another measurement is using the session, wait for it to complete.
                # Specify a timeout to aid in debugging missed unreserve calls.
                # Long measurements may require a longer timeout.
                timeout=60,
            )
        )

        if len(reservation.session_info) != 1:
            measurement_service.context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Unsupported number of sessions: {len(reservation.session_info)}",
            )

        session_info = reservation.session_info[0]
        channel_names = session_info.channel_list
        pin_to_channel = {
            mapping.pin_or_relay_name: mapping.channel for mapping in session_info.channel_mappings
        }
        if trigger_source in pin_to_channel:
            trigger_source = pin_to_channel[trigger_source]

        session = stack.enter_context(_create_niscope_session(session_info))
        session.channels[""].channel_enabled = False
        session.channels[channel_names].configure_vertical(
            vertical_range,
            str_to_enum(VERTICAL_COUPLING_TO_ENUM, vertical_coupling),
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
            str_to_enum(TRIGGER_COUPLING_TO_ENUM, trigger_coupling),
            str_to_enum(TRIGGER_SLOPE_TO_ENUM, trigger_slope),
        )
        session.trigger_modifier = (
            niscope.TriggerModifier.AUTO if auto_trigger else niscope.TriggerModifier.NO_TRIGGER_MOD
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


def _create_niscope_session(
    session_info: nims.session_management.SessionInformation,
) -> niscope.Session:
    options: Dict[str, Any] = {}
    if service_options.use_simulation:
        options["simulate"] = True
        options["driver_setup"] = {"Model": "5162 (4CH)"}

    session_kwargs: Dict[str, Any] = {}
    if service_options.use_grpc_device:
        session_grpc_address = service_options.grpc_device_address

        if not session_grpc_address:
            session_grpc_channel = measurement_service.get_channel(
                provided_interface=niscope.GRPC_SERVICE_INTERFACE_NAME,
                service_class="ni.measurementlink.v1.grpcdeviceserver",
            )
        else:
            session_grpc_channel = measurement_service.channel_pool.get_channel(
                target=session_grpc_address
            )
        session_kwargs["grpc_options"] = niscope.GrpcSessionOptions(
            session_grpc_channel,
            session_name=session_info.session_name,
            initialization_behavior=niscope.SessionInitializationBehavior.AUTO,
        )

    return niscope.Session(session_info.resource_name, options=options, **session_kwargs)


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

"""NI-DCPower MeasurementLink test service."""

import pathlib
from contextlib import ExitStack
from typing import Iterable, Sequence, Tuple

import hightime
import nidcpower

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDCPowerMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.PinArray1D, ["Pin1"])
@measurement_service.configuration("multi_session", nims.DataType.Boolean, False)
@measurement_service.output("session_names", nims.DataType.StringArray1D)
@measurement_service.output("resource_names", nims.DataType.StringArray1D)
@measurement_service.output("channel_lists", nims.DataType.StringArray1D)
@measurement_service.output("connected_channels", nims.DataType.StringArray1D)
@measurement_service.output("voltage_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("current_measurements", nims.DataType.DoubleArray1D)
def measure(
    pin_names: Iterable[str],
    multi_session: bool,
) -> Tuple[
    Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[float], Iterable[float]
]:
    """NI-DCPower MeasurementLink test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.initialize_nidcpower_sessions() as session_infos:
                connections = reservation.get_nidcpower_connections(pin_names)
                assert all([session_info.session is not None for session_info in session_infos])
                voltage_measurements, current_measurements = _source_measure_dc_voltage(connections)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                    voltage_measurements,
                    current_measurements,
                )
    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.initialize_nidcpower_session() as session_info:
                connection = reservation.get_nidcpower_connection(list(pin_names)[0])
                assert session_info.session is not None
                voltage_measurements, current_measurements = _source_measure_dc_voltage(
                    [connection]
                )

                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                    [list(voltage_measurements)[0]],
                    [list(current_measurements)[0]],
                )


def _source_measure_dc_voltage(
    connections: Sequence[nims.session_management.TypedConnection[nidcpower.Session]],
) -> Tuple[Iterable[float], Iterable[float]]:
    for connection in connections:
        channel = connection.session.channels[connection.channel_name]
        channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
        channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        channel.current_limit = 0.01
        channel.voltage_level_range = 10.0
        channel.current_limit_range = 0.01
        channel.source_delay = hightime.timedelta(seconds=0.1)
        channel.voltage_level = 5.0

    voltage_measurements, current_measurements = [], []
    with ExitStack() as stack:
        for connection in connections:
            channel = connection.session.channels[connection.channel_name]
            stack.enter_context(channel.initiate())

        for connection in connections:
            channel = connection.session.channels[connection.channel_name]
            channel.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE, timeout=10.0)

        for connection in connections:
            channel = connection.session.channels[connection.channel_name]
            measurement = channel.measure_multiple()[0]
            voltage_measurements.append(measurement.voltage)
            current_measurements.append(measurement.current)

    return (voltage_measurements, current_measurements)

"""NI-DAQmx MeasurementLink test service."""
import pathlib
from typing import List, Sequence, Tuple

import nidaqmx

import ni_measurementlink_service as nims
from ni_measurementlink_service.session_management import TypedSessionInformation


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDAQmxMeasurement.serviceconfig",
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
@measurement_service.output("voltage_values", nims.DataType.DoubleArray1D)
def measure(
    pin_names: List[str],
    multi_session: bool,
) -> Tuple[List[str], List[str], List[str], List[str], List[float]]:
    """NI-DAQmx MeasurementLink test service."""
    if multi_session:
        with measurement_service.context.reserve_sessions(pin_names) as reservation:
            with reservation.create_nidaqmx_tasks() as session_infos:
                connections = reservation.get_nidaqmx_connections(pin_names)
                assert all([session_info.session is not None for session_info in session_infos])
                voltage_values = _read_voltage_values(session_infos)

                return (
                    [session_info.session_name for session_info in session_infos],
                    [session_info.resource_name for session_info in session_infos],
                    [session_info.channel_list for session_info in session_infos],
                    [connection.channel_name for connection in connections],
                    voltage_values,
                )

    else:
        with measurement_service.context.reserve_session(pin_names) as reservation:
            with reservation.create_nidaqmx_task() as session_info:
                connection = reservation.get_nidaqmx_connection(list(pin_names)[0])
                assert session_info.session is not None
                voltage_values = _read_voltage_values([session_info])

                return (
                    [session_info.resource_name],
                    [session_info.resource_name],
                    [session_info.channel_list],
                    [connection.channel_name],
                    voltage_values,
                )


def _read_voltage_values(
    session_infos: Sequence[TypedSessionInformation[nidaqmx.Task]],
) -> List[float]:
    sample_rate = 1000.0
    number_of_samples = 2

    voltage_values = []
    for session_info in session_infos:
        task = session_info.session

        # If we created a new DAQmx task, we must also add channels to it.
        if not session_info.session_exists:
            task.ai_channels.add_ai_voltage_chan(session_info.channel_list)

        task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            samps_per_chan=number_of_samples,
        )

    for session_info in session_infos:
        session_info.session.start()

    for session_info in session_infos:
        task = session_info.session
        timeout = min(measurement_service.context.time_remaining, 10.0)
        voltage_value = task.read(number_of_samples, timeout)
        voltage_values.extend(voltage_value)

    for session_info in session_infos:
        session_info.session.stop()

    return voltage_values

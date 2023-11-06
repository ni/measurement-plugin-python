"""NI-DMM MeasurementLink test service."""
import math
import pathlib
from enum import Enum
from typing import Iterable, Sequence, Tuple

import nidmm

import ni_measurementlink_service as nims


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "NIDMMMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


class Function(Enum):
    """Wrapper enum that contains a zero value."""

    NONE = 0
    DC_VOLTS = nidmm.Function.DC_VOLTS.value
    AC_VOLTS = nidmm.Function.AC_VOLTS.value
    DC_CURRENT = nidmm.Function.DC_CURRENT.value
    AC_CURRENT = nidmm.Function.AC_CURRENT.value
    TWO_WIRE_RES = nidmm.Function.TWO_WIRE_RES.value
    FOUR_WIRE_RES = nidmm.Function.FOUR_WIRE_RES.value
    FREQ = nidmm.Function.FREQ.value
    PERIOD = nidmm.Function.PERIOD.value
    TEMPERATURE = nidmm.Function.TEMPERATURE.value
    AC_VOLTS_DC_COUPLED = nidmm.Function.AC_VOLTS_DC_COUPLED.value
    DIODE = nidmm.Function.DIODE.value
    WAVEFORM_VOLTAGE = nidmm.Function.WAVEFORM_VOLTAGE.value
    WAVEFORM_CURRENT = nidmm.Function.WAVEFORM_CURRENT.value
    CAPACITANCE = nidmm.Function.CAPACITANCE.value
    INDUCTANCE = nidmm.Function.INDUCTANCE.value


@measurement_service.register_measurement
@measurement_service.configuration("pin_names", nims.DataType.PinArray1D, ["Pin1"])
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
) -> Tuple[
    Iterable[str], Iterable[str], Iterable[str], Iterable[str], Iterable[bool], Iterable[float]
]:
    """NI-DMM MeasurementLink test service."""
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
                    [list(signals_out_of_range)[0]],
                    [list(absolute_resolutions)[0]],
                )


def _get_dmm_readings(
    session_infos: Sequence[nims.session_management.TypedSessionInformation[nidmm.Session]],
) -> Tuple[Iterable[bool], Iterable[float]]:
    nidmm_function = nidmm.Function(Function.DC_VOLTS.value)
    range = 10.0
    resolution_digits = 5.5

    signals_out_of_range, absolute_resolutions = [], []
    for session_info in session_infos:
        session = session_info.session
        session.configure_measurement_digits(nidmm_function, range, resolution_digits)
        measured_value = session.read()
        signal_out_of_range = math.isnan(measured_value) or math.isinf(measured_value)
        absolute_resolution = session.resolution_absolute
        signals_out_of_range.append(signal_out_of_range)
        absolute_resolutions.append(absolute_resolution)

    return (signals_out_of_range, absolute_resolutions)

from unittest.mock import Mock

import measurement
import nidmm
import pytest

from ni_measurementlink_service.session_management import (
    INSTRUMENT_TYPE_NI_DMM,
    ChannelMapping,
    PinMapContext,
    SessionInformation,
)


def test___measurement_logic___measure___configures_and_reads_dmm(
    measurement_context: Mock,
    single_session_reservation: Mock,
    nidmm_session: Mock,
) -> None:
    measurement_context.pin_map_context = PinMapContext("mypinmap", sites=[0])
    single_session_reservation.session_info = SessionInformation(
        "MySession",
        "DMM1",
        "0",
        INSTRUMENT_TYPE_NI_DMM,
        False,
        [ChannelMapping("Pin1", site=0, channel="0")],
    )
    nidmm_session.read.return_value = 1.2345
    nidmm_session.resolution_absolute = 100e-6

    measured_value, signal_out_of_range, absolute_resolution = measurement.measure(
        pin_name="Pin1",
        measurement_type=measurement.Function.DC_VOLTS,
        range=10.0,
        resolution_digits=5.5,
    )

    nidmm_session.configure_measurement_digits.assert_called_once_with(
        nidmm.Function.DC_VOLTS, 10.0, 5.5
    )
    nidmm_session.read.assert_called_once()
    assert measured_value == pytest.approx(1.2345)
    assert not signal_out_of_range
    assert absolute_resolution == pytest.approx(100e-6)

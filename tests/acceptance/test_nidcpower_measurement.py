import pathlib
from typing import Generator, Iterable, NamedTuple

import pytest

from ni_measurement_plugin._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2 import (
    MeasureRequest,
)
from ni_measurement_plugin._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2_grpc import (
    MeasurementServiceStub,
)
from ni_measurement_plugin._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurement_plugin.measurement.service import MeasurementService
from tests.utilities.measurements import nidcpower_measurement
from tests.utilities.pin_map_client import PinMapClient
from tests.utilities.stubs.nidcpower.types_pb2 import Configurations, Outputs

_SITE = 0


def test___single_session___measure___returns_measured_values(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.voltage_measurements == [5]
    assert outputs.current_measurements == [0.0001]


def test___single_session___measure___creates_single_session(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("DCPower1/0", "DCPower1/0", "DCPower1/0", "DCPower1/0")
    ]


def test___multiple_sessions___measure___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1", "Pin2"], multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("DCPower1/0", "DCPower1/0", "DCPower1/0", "DCPower1/0"),
        _MeasurementOutput("DCPower1/2", "DCPower1/2", "DCPower1/2", "DCPower1/2"),
    ]


def _measure(
    stub_v2: MeasurementServiceStub,
    pin_map_context: PinMapContext,
    configurations: Configurations,
) -> Outputs:
    request = MeasureRequest(pin_map_context=pin_map_context)
    request.configuration_parameters.Pack(configurations)
    response_iterator = stub_v2.Measure(request)
    responses = list(response_iterator)
    assert len(responses) == 1
    outputs = Outputs.FromString(responses[0].outputs.value)
    return outputs


@pytest.fixture(scope="module")
def measurement_service() -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with nidcpower_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "1Smu2ChannelGroup2Pin1Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

    return PinMapContext(pin_map_id=pin_map_id, sites=[_SITE])


class _MeasurementOutput(NamedTuple):
    session_name: str
    resource_name: str
    channel_list: str
    connected_channels: str


def _get_output(outputs: Outputs) -> Iterable[_MeasurementOutput]:
    return [
        _MeasurementOutput(session_name, resource_name, channel_list, connected_channels)
        for session_name, resource_name, channel_list, connected_channels in zip(
            outputs.session_names,
            outputs.resource_names,
            outputs.channel_lists,
            outputs.connected_channels,
        )
    ]

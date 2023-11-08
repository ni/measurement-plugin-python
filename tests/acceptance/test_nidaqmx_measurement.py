import pathlib
from typing import Generator, Iterable, NamedTuple

import pytest

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2 import (
    MeasureRequest,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2_grpc import (
    MeasurementServiceStub,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurementlink_service.measurement.service import MeasurementService
from tests.assets.stubs.nidaqmx_measurement.types_pb2 import (
    Configurations,
    Outputs,
)
from tests.utilities import nidaqmx_measurement
from tests.utilities.pin_map_client import PinMapClient

_SITE = 0


def test___single_session___measure___returns_measured_values(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_names = ["Pin1"]
    min_value = -10.5
    max_value = 10.5
    configurations = Configurations(pin_names=pin_names, multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert min_value <= outputs.voltage_values[0] <= max_value


def test___single_session___measure___creates_single_session(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_names = ["Pin1"]
    configurations = Configurations(pin_names=pin_names, multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [_MeasurementOutput("Dev1", "Dev1", "Dev1/ai0", "Dev1/ai0")]


def test___multiple_sessions___measure___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_names = ["Pin1", "Pin2"]
    configurations = Configurations(pin_names=pin_names, multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("Dev1", "Dev1", "Dev1/ai0", "Dev1/ai0"),
        _MeasurementOutput("Dev2", "Dev2", "Dev2/ai0", "Dev2/ai0"),
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
    with nidaqmx_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "2Mio2Pin1Site.pinmap"
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

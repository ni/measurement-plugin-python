from __future__ import annotations

import pathlib
from collections.abc import Generator, Iterable
from typing import NamedTuple

import pytest

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2 import (
    MeasureRequest,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2_grpc import (
    MeasurementServiceStub,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from tests.utilities.measurements import niswitch_multiplexer_measurement
from tests.utilities.stubs.niswitchmultiplexer.types_pb2 import Configurations, Outputs

_SITE = 0


pytestmark = pytest.mark.usefixtures("filter_wrong_configurations_message_type_warnings")


def test___single_session___measure___creates_single_session(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["A"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("Multiplexer1", "Multiplexer1", "b0c1->b0r0", "DCPower1/0")
    ]


def test___multiple_sessions___measure___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["A", "B"], multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("Multiplexer1", "Multiplexer1", "b0c1->b0r0", "DCPower1/0"),
        _MeasurementOutput("Multiplexer2", "Multiplexer2", "b0c3->b0r0", "DCPower1/2"),
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
def measurement_service() -> Generator[MeasurementService]:
    """Test fixture that creates and hosts a measurement service."""
    with niswitch_multiplexer_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "2SwitchMultiplexer1Smu2Pin1Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)

    return PinMapContext(pin_map_id=pin_map_id, sites=[_SITE])


class _MeasurementOutput(NamedTuple):
    multiplexer_session_name: str
    multiplexer_resource_name: str
    multiplexer_route: str
    connected_channel: str


def _get_output(outputs: Outputs) -> Iterable[_MeasurementOutput]:
    return [
        _MeasurementOutput(session_name, resource_name, multiplexer_route, connected_channel)
        for session_name, resource_name, multiplexer_route, connected_channel in zip(
            outputs.multiplexer_session_names,
            outputs.multiplexer_resource_names,
            outputs.multiplexer_routes,
            outputs.connected_channels,
        )
    ]

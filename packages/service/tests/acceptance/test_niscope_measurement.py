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
from tests.utilities.measurements import niscope_measurement
from tests.utilities.stubs.niscope.types_pb2 import Configurations, Outputs

_SITE = 0


pytestmark = pytest.mark.usefixtures("filter_wrong_configurations_message_type_warnings")


def test___single_session___measure___returns_measured_values(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert all([-2.5 < sample < 2.5 for sample in outputs.waveform])


def test___single_session___measure___creates_single_session(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [_MeasurementOutput("SCOPE1", "SCOPE1", "0", "0")]


def test___multiple_sessions___measure___creates_multiple_sessions(
    pin_map_context: PinMapContext,
    stub_v2: MeasurementServiceStub,
) -> None:
    configurations = Configurations(pin_names=["Pin1", "Pin2"], multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput("SCOPE1", "SCOPE1", "0", "0"),
        _MeasurementOutput("SCOPE2", "SCOPE2", "0", "0"),
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
    with niscope_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_context(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> PinMapContext:
    pin_map_name = "2Scope2Pin2Group1Site.pinmap"
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

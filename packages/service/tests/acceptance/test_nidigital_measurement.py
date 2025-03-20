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
from tests.utilities.measurements import nidigital_measurement
from tests.utilities.stubs.nidigital.types_pb2 import Configurations, Outputs

pytestmark = pytest.mark.usefixtures("filter_wrong_configurations_message_type_warnings")


def test___single_session___measure___returns_measured_values(
    pin_map_id: str,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    configurations = Configurations(pin_names=["CS", "SCLK", "MOSI", "MISO"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.passing_sites == [0]
    assert outputs.failing_sites == []


def test___single_session___measure___creates_single_session(
    pin_map_id: str,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    configurations = Configurations(pin_names=["CS", "SCLK", "MOSI", "MISO"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput(
            "DigitalPattern1",
            "DigitalPattern1",
            "site0/CS, site0/SCLK, site0/MOSI, site0/MISO",
            "site0/CS",
        )
    ]


def test___multiple_sessions___measure___creates_multiple_sessions(
    pin_map_id: str,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
    configurations = Configurations(pin_names=["CS", "SCLK", "MOSI", "MISO"], multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert _get_output(outputs) == [
        _MeasurementOutput(
            "DigitalPattern1",
            "DigitalPattern1",
            "site0/CS, site0/SCLK, site0/MOSI, site0/MISO",
            "site0/CS, site0/SCLK, site0/MOSI, site0/MISO",
        ),
        _MeasurementOutput(
            "DigitalPattern2",
            "DigitalPattern2",
            "site1/CS, site1/SCLK, site1/MOSI, site1/MISO",
            "site1/CS, site1/SCLK, site1/MOSI, site1/MISO",
        ),
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
    with nidigital_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_id(pin_map_client: PinMapClient, pin_map_directory: pathlib.Path) -> str:
    pin_map_name = "2Digital2Group4Pin1Site.pinmap"
    return pin_map_client.update_pin_map(pin_map_directory / pin_map_name)


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

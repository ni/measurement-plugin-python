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
from tests.assets import nidcpower_measurement_pb2
from tests.utilities import nidcpower_measurement
from tests.utilities.pin_map_client import PinMapClient


class Configuration(NamedTuple):
    """A group of shared test parameters."""

    pin_map_name: str
    pin_names: Iterable[str]
    sites: Iterable[int]
    expected_session_names: Iterable[str]
    expected_resource_names: Iterable[str]
    expected_channel_lists: Iterable[str]


_SMU_SINGLE_SESSION_CONFIGURATIONS = [
    Configuration(
        "1Smu1ChannelGroup1Pin1Site.pinmap",
        ["Pin1"],
        [0],
        ["DCPower1/0"],
        ["DCPower1/0"],
        ["DCPower1/0"],
    ),
    Configuration(
        "1Smu1ChannelGroup2Pin2Site.pinmap",
        ["Pin1"],
        [0],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0"],
    ),
    Configuration(
        "1Smu1ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1"],
    ),
    Configuration(
        "1Smu1ChannelGroup2Pin2Site.pinmap",
        ["Pin1"],
        [0, 1],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/2"],
    ),
    Configuration(
        "1Smu1ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0, 1],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1, DCPower1/2, DCPower1/3"],
    ),
    Configuration(
        "1Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1"],
        [0],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0"],
    ),
    Configuration(
        "1Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
    ),
    Configuration(
        "1Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [1],
        ["DCPower1/2, DCPower1/3"],
        ["DCPower1/2, DCPower1/3"],
        ["DCPower1/2, DCPower1/3"],
    ),
    Configuration(
        "2Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1"],
        [0],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0"],
    ),
    Configuration(
        "2Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
        ["DCPower1/0, DCPower1/1"],
    ),
    Configuration(
        "2Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [1],
        ["DCPower2/0, DCPower2/1"],
        ["DCPower2/0, DCPower2/1"],
        ["DCPower2/0, DCPower2/1"],
    ),
]


@pytest.mark.parametrize("configuration", _SMU_SINGLE_SESSION_CONFIGURATIONS)
def test___single_session___measure___single_session_created(
    configuration: Configuration,
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / configuration.pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=configuration.sites)
    configurations = nidcpower_measurement_pb2.NIDCPowerConfigurations(
        pin_names=configuration.pin_names, multi_session=False
    )

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.session_names == configuration.expected_session_names
    assert outputs.resource_names == configuration.expected_resource_names
    assert outputs.channel_lists == configuration.expected_channel_lists


def _measure(
    stub_v2: MeasurementServiceStub,
    pin_map_context: PinMapContext,
    configurations: nidcpower_measurement_pb2.NIDCPowerConfigurations,
) -> nidcpower_measurement_pb2.NIDCPowerOutputs:
    request = MeasureRequest(pin_map_context=pin_map_context)
    request.configuration_parameters.Pack(configurations)
    response_iterator = stub_v2.Measure(request)
    responses = list(response_iterator)
    assert len(responses) == 1
    outputs = nidcpower_measurement_pb2.NIDCPowerOutputs.FromString(responses[0].outputs.value)
    return outputs


@pytest.fixture(scope="module")
def measurement_service() -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with nidcpower_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "acceptance" / "session_management"

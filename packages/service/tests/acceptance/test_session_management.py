from __future__ import annotations

import pathlib
from collections.abc import Generator, Iterable
from typing import NamedTuple

import grpc
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
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import pin_aware_measurement
from tests.utilities.stubs.pinaware.types_pb2 import Configurations, Outputs

pytestmark = pytest.mark.usefixtures("filter_wrong_configurations_message_type_warnings")


def test___pin_map_context___measure___sends_pin_map_id_and_sites(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
    pin_map_id = pin_map_client.update_pin_map(pin_map_path)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0, 1])
    configurations = Configurations(pin_names=["Pin1", "Pin2"], multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.pin_map_id == pin_map_id
    assert outputs.sites == pin_map_context.sites


class Configuration(NamedTuple):
    """A group of shared test parameters."""

    pin_map_name: str
    pin_names: Iterable[str]
    sites: Iterable[int]
    expected_session_names: Iterable[str]
    expected_resource_names: Iterable[str]
    expected_channel_lists: Iterable[str]


_FGEN_SINGLE_SESSION_CONFIGURATIONS = [
    Configuration(
        "1Fgen1Pin1Site.pinmap",
        ["Pin1"],
        [0],
        ["FGEN1"],
        ["FGEN1"],
        ["0"],
    ),
    Configuration(
        "2Fgen2Pin2Site.pinmap",
        ["Pin1"],
        [0],
        ["FGEN1"],
        ["FGEN1"],
        ["0"],
    ),
    Configuration(
        "2Fgen2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0],
        ["FGEN1"],
        ["FGEN1"],
        ["0, 1"],
    ),
    Configuration(
        "2Fgen2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [1],
        ["FGEN2"],
        ["FGEN2"],
        ["0, 1"],
    ),
]

_FGEN_MULTI_SESSION_CONFIGURATIONS = [
    Configuration(
        "2Fgen2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0, 1],
        ["FGEN1", "FGEN2"],
        ["FGEN1", "FGEN2"],
        ["0, 1", "0, 1"],
    ),
]

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

_SMU_MULTI_SESSION_CONFIGURATIONS = [
    Configuration(
        "1Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0, 1],
        ["DCPower1/0, DCPower1/1", "DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1", "DCPower1/2, DCPower1/3"],
        ["DCPower1/0, DCPower1/1", "DCPower1/2, DCPower1/3"],
    ),
    Configuration(
        "2Smu2ChannelGroup2Pin2Site.pinmap",
        ["Pin1", "Pin2"],
        [0, 1],
        ["DCPower1/0, DCPower1/1", "DCPower2/0, DCPower2/1"],
        ["DCPower1/0, DCPower1/1", "DCPower2/0, DCPower2/1"],
        ["DCPower1/0, DCPower1/1", "DCPower2/0, DCPower2/1"],
    ),
]


@pytest.mark.parametrize(
    "configuration", _FGEN_SINGLE_SESSION_CONFIGURATIONS + _SMU_SINGLE_SESSION_CONFIGURATIONS
)
def test___single_session___measure___reserves_single_session(
    configuration: Configuration,
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / configuration.pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=configuration.sites)
    configurations = Configurations(pin_names=configuration.pin_names, multi_session=False)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.session_names == configuration.expected_session_names
    assert outputs.resource_names == configuration.expected_resource_names
    assert outputs.channel_lists == configuration.expected_channel_lists


@pytest.mark.parametrize(
    "configuration",
    _FGEN_SINGLE_SESSION_CONFIGURATIONS
    + _FGEN_MULTI_SESSION_CONFIGURATIONS
    + _SMU_SINGLE_SESSION_CONFIGURATIONS
    + _SMU_MULTI_SESSION_CONFIGURATIONS,
)
def test___multi_session___measure___reserves_multiple_sessions(
    configuration: Configuration,
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / configuration.pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=configuration.sites)
    configurations = Configurations(pin_names=configuration.pin_names, multi_session=True)

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.session_names == configuration.expected_session_names
    assert outputs.resource_names == configuration.expected_resource_names
    assert outputs.channel_lists == configuration.expected_channel_lists


@pytest.mark.parametrize(
    "configuration", _FGEN_MULTI_SESSION_CONFIGURATIONS + _SMU_MULTI_SESSION_CONFIGURATIONS
)
def test___multi_session_but_expecting_single_session___measure___raises_too_many_sessions_error(
    configuration: Configuration,
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / configuration.pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=configuration.sites)
    configurations = Configurations(pin_names=configuration.pin_names, multi_session=False)

    with pytest.raises(grpc.RpcError) as exc_info:
        _ = _measure(stub_v2, pin_map_context, configurations)

    assert exc_info.value.code() == grpc.StatusCode.UNKNOWN
    assert "Too many sessions reserved." in (exc_info.value.details() or "")


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
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService]:
    """Test fixture that creates and hosts a measurement service."""
    with pin_aware_measurement.measurement_service.host_service() as service:
        yield service

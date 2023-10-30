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


def test___single_session___measure___single_session_created(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    stub_v2: MeasurementServiceStub,
) -> None:
    
    pin_map_name = "1Smu1ChannelGroup1Pin1Site.pinmap"
    pin_names = ["Pin1"]
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    configurations = nidcpower_measurement_pb2.NIDCPowerConfigurations(
        pin_names=pin_names, multi_session=False
    )

    outputs = _measure(stub_v2, pin_map_context, configurations)

    assert outputs.session_names == ["DCPower1/0"]
    assert outputs.resource_names == ["DCPower1/0"]
    assert outputs.channel_lists == ["DCPower1/0"]


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

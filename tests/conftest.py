"""Pytest configuration file."""
import pathlib
import sys
from typing import Generator, List

import grpc
import pytest

from ni_measurementlink_service._featuretoggles import FeatureToggle
from ni_measurementlink_service._internal.discovery_client import (
    DiscoveryClient,
    _get_registration_json_file_path,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import (
    GrpcChannelPool,
    MeasurementService,
)
from ni_measurementlink_service.session_management import SessionManagementClient
from tests.utilities.discovery_service_process import DiscoveryServiceProcess


@pytest.fixture(scope="module")
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "assets"


@pytest.fixture
def grpc_channel(measurement_service: MeasurementService) -> Generator[grpc.Channel, None, None]:
    """Test fixture that creates a gRPC channel."""
    target = measurement_service.service_location.insecure_address
    options = [
        ("grpc.max_receive_message_length", -1),
        ("grpc.max_send_message_length", -1),
    ]
    with grpc.insecure_channel(target, options) as channel:
        yield channel


@pytest.fixture
def stub_v1(grpc_channel: grpc.Channel) -> v1_measurement_service_pb2_grpc.MeasurementServiceStub:
    """Test fixture that creates a MeasurementService v1 stub."""
    return v1_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)


@pytest.fixture
def stub_v2(grpc_channel: grpc.Channel) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    """Test fixture that creates a MeasurementService v2 stub."""
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)


@pytest.fixture(scope="session")
def discovery_service_process() -> Generator[DiscoveryServiceProcess, None, None]:
    """Test fixture that creates discovery service process."""
    if sys.platform != "win32":
        pytest.skip(
            f"Platform {sys.platform} is not supported for starting discovery service."
            "Could not proceed to run the tests."
        )
    elif not _get_registration_json_file_path().exists():
        pytest.skip(
            "MeasurementLink registration file not found or MeasurementLink not installed."
            "Could not proceed to run the tests. Install MeasurementLink to create the registration file."
        )
    else:
        with DiscoveryServiceProcess() as proc:
            yield proc


@pytest.fixture(scope="session")
def grpc_channel_pool() -> Generator[GrpcChannelPool, None, None]:
    """Test fixture that creates a gRPC channel pool."""
    with GrpcChannelPool() as grpc_channel_pool:
        yield grpc_channel_pool


@pytest.fixture
def discovery_client(
    discovery_service_process: DiscoveryServiceProcess, grpc_channel_pool: GrpcChannelPool
) -> DiscoveryClient:
    """Test fixture that creates a discovery client."""
    return DiscoveryClient(grpc_channel_pool=grpc_channel_pool)


@pytest.fixture
def session_management_client(
    discovery_client: DiscoveryClient, grpc_channel_pool: GrpcChannelPool
) -> SessionManagementClient:
    """Test fixture that creates a session management client."""
    return SessionManagementClient(
        discovery_client=discovery_client, grpc_channel_pool=grpc_channel_pool
    )


@pytest.fixture
def feature_toggles(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Test fixture that disables or enables feature toggles."""
    for mark in request.node.iter_markers():
        if mark.name in ["disable_feature_toggle", "enable_feature_toggle"]:
            feature_toggle = mark.args[0]
            assert isinstance(feature_toggle, FeatureToggle)
            monkeypatch.setattr(feature_toggle, "is_enabled", mark.name == "enable_feature_toggle")


def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    """Hook to inject fixtures based on marks."""
    for item in items:
        if item.get_closest_marker("disable_feature_toggle") or item.get_closest_marker(
            "enable_feature_toggle"
        ):
            assert hasattr(item, "fixturenames")
            item.fixturenames.append("feature_toggles")

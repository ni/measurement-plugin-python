"""Contains tests to validate the discovery_client.py.
"""
from typing import cast

import pytest

from ni_measurementlink_service._internal.discovery_client import (
    DiscoveryClient,
    _PROVIDED_MEASUREMENT_SERVICE,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2_grpc import (
    DiscoveryServiceStub,
)
from ni_measurementlink_service.measurement.info import ServiceInfo, MeasurementInfo
from tests.utilities.fake_discovery_service import (
    FakeDiscoveryServiceStub,
)


_TEST_SERVICE_PORT = "9999"
_TEST_SERVICE_INFO = ServiceInfo("TestServiceClass", "TestUrl")
_TEST_MEASUREMENT_INFO = MeasurementInfo(
    display_name="TestMeasurement",
    version="1.0.0.0",
    ui_file_paths=[],
)


def test___discovery_service_available___register_service___registration_success(
    discovery_client: DiscoveryClient, discovery_service_stub: FakeDiscoveryServiceStub
):
    registration_success_flag = discovery_client.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_MEASUREMENT_INFO
    )

    _validate_grpc_request(discovery_service_stub.request)
    assert registration_success_flag


def test___discovery_service_available___unregister_registered_service___unregistration_success(
    discovery_client: DiscoveryClient,
):
    discovery_client.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_MEASUREMENT_INFO
    )

    unregistration_success_flag = discovery_client.unregister_service()

    assert unregistration_success_flag


def test___discovery_service_available___unregister_non_registered_service___unregistration_failure(
    discovery_client: DiscoveryClient,
):
    unregistration_success_flag = discovery_client.unregister_service()

    assert ~unregistration_success_flag  # False


def test___discovery_service_unavailable___register_service_registration_failure(
    discovery_client: DiscoveryClient,
):
    discovery_client.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_MEASUREMENT_INFO
    )

    unregistration_success_flag = discovery_client.unregister_service()

    assert ~unregistration_success_flag  # False


@pytest.fixture
def discovery_client(discovery_service_stub: FakeDiscoveryServiceStub) -> DiscoveryClient:
    """Create a DiscoveryClient."""
    return DiscoveryClient(cast(DiscoveryServiceStub, discovery_service_stub))


@pytest.fixture
def discovery_service_stub() -> FakeDiscoveryServiceStub:
    """Create a FakeDiscoveryServiceStub."""
    return FakeDiscoveryServiceStub()


def _validate_grpc_request(request):
    assert request.location.insecure_port == _TEST_SERVICE_PORT
    assert request.location.location == "localhost"
    assert request.service_description.service_class == _TEST_SERVICE_INFO.service_class
    assert request.service_description.description_url == _TEST_SERVICE_INFO.description_url
    assert request.service_description.display_name == _TEST_MEASUREMENT_INFO.display_name
    assert _PROVIDED_MEASUREMENT_SERVICE in request.service_description.provided_interfaces

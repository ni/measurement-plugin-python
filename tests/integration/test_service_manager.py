"""Contains test to validate service_manager.py."""
from typing import cast

import grpc
import pytest

from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.service_manager import GrpcService
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2_grpc import (
    DiscoveryServiceStub,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2,
    measurement_service_pb2_grpc,
)
from tests.utilities import loopback_measurement
from tests.utilities.fake_discovery_service import (
    FakeDiscoveryServiceStub,
    FakeDiscoveryServiceStubError,
)


def test___grpc_service___start_service___service_hosted(grpc_service: GrpcService):
    port_number = grpc_service.start(
        loopback_measurement.measurement_service.measurement_info,
        loopback_measurement.measurement_service.service_info,
        loopback_measurement.measurement_service.configuration_parameter_list,
        loopback_measurement.measurement_service.output_parameter_list,
        loopback_measurement.measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


def test___grpc_service_without_discovery_service___start_service___service_hosted(
    grpc_service: GrpcService,
):
    port_number = grpc_service.start(
        loopback_measurement.measurement_service.measurement_info,
        loopback_measurement.measurement_service.service_info,
        loopback_measurement.measurement_service.configuration_parameter_list,
        loopback_measurement.measurement_service.output_parameter_list,
        loopback_measurement.measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


@pytest.mark.parametrize("expect_discovery_service_error_stub", [True])
def test___grpc_service___start_service_error_registering_measurement___raises_error(
    grpc_service: GrpcService,
):
    with pytest.raises(Exception):
        grpc_service.start(
            loopback_measurement.measurement_service.measurement_info,
            loopback_measurement.measurement_service.service_info,
            loopback_measurement.measurement_service.configuration_parameter_list,
            loopback_measurement.measurement_service.output_parameter_list,
            loopback_measurement.measurement_service.measure_function,
        )


def test___grpc_service_started___stop_service___service_stopped(grpc_service: GrpcService):
    port_number = grpc_service.start(
        loopback_measurement.measurement_service.measurement_info,
        loopback_measurement.measurement_service.service_info,
        loopback_measurement.measurement_service.configuration_parameter_list,
        loopback_measurement.measurement_service.output_parameter_list,
        loopback_measurement.measurement_service.measure_function,
    )

    grpc_service.stop()

    with pytest.raises(Exception):
        _validate_if_service_running_by_making_rpc(port_number)


@pytest.fixture
def grpc_service(discovery_client: DiscoveryClient) -> GrpcService:
    """Create a GrpcService."""
    return GrpcService(discovery_client)


@pytest.fixture
def discovery_client(discovery_service_stub: FakeDiscoveryServiceStub) -> DiscoveryClient:
    """Create a DiscoveryClient."""
    return DiscoveryClient(cast(DiscoveryServiceStub, discovery_service_stub))


@pytest.fixture
def discovery_service_stub(expect_discovery_service_error_stub: bool) -> FakeDiscoveryServiceStub:
    """Create a valid/error stub based on expect_discovery_service_error_stub value."""
    return (
        FakeDiscoveryServiceStubError()
        if expect_discovery_service_error_stub
        else FakeDiscoveryServiceStub()
    )


@pytest.fixture
def expect_discovery_service_error_stub() -> bool:
    """Boolean to choose between FakeDiscoveryServiceStub and FakeDiscoveryServiceStubError."""
    return False


def _validate_if_service_running_by_making_rpc(port_number):
    """Implicit validation of running service.

    Throws exception during RPC if service not hosted.
    """
    with grpc.insecure_channel("localhost:" + port_number) as channel:
        stub = measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        stub.GetMetadata(measurement_service_pb2.GetMetadataRequest())  # RPC call

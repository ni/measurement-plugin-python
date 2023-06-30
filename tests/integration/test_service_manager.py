"""Contains test to validate service_manager.py."""
from typing import cast

import grpc
import pytest
from examples.sample_measurement import measurement

from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.service_manager import GrpcService
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2_grpc import (
    DiscoveryServiceStub,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2,
    measurement_service_pb2_grpc,
)
from tests.utilities.fake_discovery_service import FakeDiscoveryServiceStub


@pytest.mark.skip(reason="blah blah")
def test___grpc_service___start_service___service_hosted(grpc_service: GrpcService):
    port_number = grpc_service.start(
        measurement.sample_measurement_service.measurement_info,
        measurement.sample_measurement_service.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


def test___grpc_service_without_discovery_service___start_service___service_hosted(
    grpc_service: GrpcService,
):
    port_number = grpc_service.start(
        measurement.sample_measurement_service.measurement_info,
        measurement.sample_measurement_service.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


def test___grpc_service_started___stop_service___service_stopped(grpc_service: GrpcService):
    port_number = grpc_service.start(
        measurement.sample_measurement_service.measurement_info,
        measurement.sample_measurement_service.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
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
def discovery_service_stub() -> FakeDiscoveryServiceStub:
    """Create a FakeDiscoveryServiceStub."""
    return FakeDiscoveryServiceStub()


def _validate_if_service_running_by_making_rpc(port_number):
    """Implicit validation of running service.

    Throws exception during RPC if service not hosted.
    """
    with grpc.insecure_channel("localhost:" + port_number) as channel:
        stub = measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        stub.GetMetadata(measurement_service_pb2.GetMetadataRequest())  # RPC call

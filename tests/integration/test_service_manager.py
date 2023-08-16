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


@pytest.mark.expect_discovery_service_stub_error(True)
def test___grpc_service___start_service_error_registering_measurement___raises_type_error(
    grpc_service: GrpcService,
):
    port_number = grpc_service.start(
        loopback_measurement.measurement_service.measurement_info,
        loopback_measurement.measurement_service.service_info,
        loopback_measurement.measurement_service.configuration_parameter_list,
        loopback_measurement.measurement_service.output_parameter_list,
        loopback_measurement.measurement_service.measure_function,
    )

    with pytest.raises(Exception):
        _validate_if_service_running_by_making_rpc(port_number)

    assert not port_number


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
def discovery_service_stub(request) -> FakeDiscoveryServiceStub:
    """Create a valid or error FakeDiscoveryServiceStub."""
    expect_discovery_service_stub_error = _get_marker_value(
        request, "expect_discovery_service_stub_error"
    )
    if expect_discovery_service_stub_error:
        return FakeDiscoveryServiceStubError()
    return FakeDiscoveryServiceStub()


def _validate_if_service_running_by_making_rpc(port_number):
    """Implicit validation of running service.

    Throws exception during RPC if service not hosted.
    """
    with grpc.insecure_channel("localhost:" + port_number) as channel:
        stub = measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        stub.GetMetadata(measurement_service_pb2.GetMetadataRequest())  # RPC call


def _get_marker_value(request, marker_name, default=None):
    """Gets the value of a pytest marker based on the marker name."""
    marker_value = default
    for marker in request.node.iter_markers():
        if marker.name == marker_name:  # only look at markers with valid argument name
            marker_value = marker.args[0]  # assume single parameter in marker

    return marker_value

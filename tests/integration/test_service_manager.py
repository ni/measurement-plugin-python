"""Contains test to validate service_manager.py."""
import grpc
import pytest
from examples.sample_measurement import measurement

from ni_measurement_service._internal.discovery_client import DiscoveryClient
from ni_measurement_service._internal.service_manager import GrpcService
from ni_measurement_service._internal.stubs import Measurement_pb2, Measurement_pb2_grpc
from tests.utilities.fake_discovery_service import (
    FakeDiscoveryServiceStub,
    FakeDiscoveryServiceStubError,
)


def test___grpc_service___start_service___service_hosted():
    """Test to validate if measurement service is started."""
    grpc_service = GrpcService(DiscoveryClient(FakeDiscoveryServiceStub()))

    port_number = grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


def test___grpc_service_without_discovery_service___start_service___service_hosted():
    """Test to validate if measurement service start when the discovery service not available."""
    grpc_service = GrpcService(DiscoveryClient(FakeDiscoveryServiceStubError()))

    port_number = grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )

    _validate_if_service_running_by_making_rpc(port_number)


def test___grpc_service_started___stop_service___service_stopped():
    """Test to validate if measurement service is stopped."""
    grpc_service = GrpcService(DiscoveryClient(FakeDiscoveryServiceStub()))
    port_number = grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )

    grpc_service.stop()

    with pytest.raises(Exception):
        _validate_if_service_running_by_making_rpc(port_number)


def _validate_if_service_running_by_making_rpc(port_number):
    """Implicit validation of running service.

    Throws exception during RPC if service not hosted.
    """
    with grpc.insecure_channel("localhost:" + port_number) as channel:
        stub = Measurement_pb2_grpc.MeasurementServiceStub(channel)
        stub.GetMetadata(Measurement_pb2.GetMetadataRequest())  # RPC call

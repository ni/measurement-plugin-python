from ni_measurement_service._internal.discovery_client import DiscoveryClient
from ni_measurement_service._internal.service_manager import GrpcService
from tests.utilities.fake_registry_service import (
    FakeRegistryServiceStub,
    FakeRegistryServiceStubError,
)
from examples.sample_measurement import measurement


def test___grpc_service___start_service___service_hosted():
    """Test to validate if measurement service is started."""
    grpc_service = GrpcService(DiscoveryClient(FakeRegistryServiceStub()))

    grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )


def test___grpc_service_without_discovery_service___start_service___service_hosted():
    """Test to validate if measurement service is started despite the discovery service not available."""
    grpc_service = GrpcService(DiscoveryClient(FakeRegistryServiceStubError()))

    grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )


def test___grpc_service_started___stop_service___service_stopped():
    """Test to validate if measurement service is stopped."""
    grpc_service = GrpcService(DiscoveryClient(FakeRegistryServiceStub()))
    grpc_service.start(
        measurement.measurement_info,
        measurement.service_info,
        measurement.sample_measurement_service.configuration_parameter_list,
        measurement.sample_measurement_service.output_parameter_list,
        measurement.sample_measurement_service.measure_function,
    )
    grpc_service.stop()

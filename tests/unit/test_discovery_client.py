"""Contains tests to validate the discovery_client.py.
"""
from ni_measurement_service._internal import discovery_client
from ni_measurement_service.measurement.info import ServiceInfo, MeasurementInfo, UIFileType
from tests.utilities.fake_registry_service import (
    FakeRegistryServiceStub,
    FakeRegistryServiceStubError,
)


_TEST_SERVICE_PORT = "9999"
_TEST_SERVICE_INFO = ServiceInfo("TestServiceClass", "TestServiceID", "TestUrl")
_TEST_DISPLAY_NAME = MeasurementInfo("TestMeasurement", ui_file_type=UIFileType.LabVIEW)


def test___discovery_service_available___register_service___registration_success():
    """Test the successful registration when the discovery service is available."""
    fake_registry_service_stub = FakeRegistryServiceStub()
    discovery_client_obj = discovery_client.DiscoveryClient(fake_registry_service_stub)

    registration_success_flag = discovery_client_obj.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_DISPLAY_NAME
    )

    _validate_grpc_request(fake_registry_service_stub.request)
    assert registration_success_flag


def test___discovery_service_available___unregister_registered_service___un_registration_success():
    """Test the successful un-registration of registered service."""
    fake_registry_service_stub = FakeRegistryServiceStub()
    discovery_client_obj = discovery_client.DiscoveryClient(fake_registry_service_stub)
    discovery_client_obj.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_DISPLAY_NAME
    )

    un_registration_success_flag = discovery_client_obj.unregister_service()

    assert un_registration_success_flag


def test___discovery_service_available___unregister_non_registered_service___un_registration_failure():
    """Test the unsuccessful un-registration of non-registered service."""
    fake_registry_service_stub = FakeRegistryServiceStub()
    discovery_client_obj = discovery_client.DiscoveryClient(fake_registry_service_stub)

    un_registration_success_flag = discovery_client_obj.unregister_service()

    assert ~un_registration_success_flag  # False


def test___discovery_service_unavailable___register_service_registration_failure():
    """Test the unsuccessful registration when discovery service is not available."""
    fake_registry_service_stub = FakeRegistryServiceStubError()
    discovery_client_obj = discovery_client.DiscoveryClient(fake_registry_service_stub)
    discovery_client_obj.register_measurement_service(
        _TEST_SERVICE_PORT, _TEST_SERVICE_INFO, _TEST_DISPLAY_NAME
    )

    un_registration_success_flag = discovery_client_obj.unregister_service()

    assert ~un_registration_success_flag  # False


def _validate_grpc_request(request):
    assert request.location.insecure_port == _TEST_SERVICE_PORT
    assert request.location.location == "localhost"
    assert request.service_description.service_id == _TEST_SERVICE_INFO.service_id
    assert request.service_description.service_class == _TEST_SERVICE_INFO.service_class
    assert request.service_description.description_url == _TEST_SERVICE_INFO.description_url
    assert request.service_description.name == _TEST_DISPLAY_NAME
    assert discovery_client._PROVIDED_MEASUREMENT_SERVICE in request.provided_services

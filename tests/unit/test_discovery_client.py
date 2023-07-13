"""Contains tests to validate the discovery_client.py.
"""
import json
import pathlib
from typing import cast

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._internal.discovery_client import (
    DiscoveryClient,
    _get_discovery_service_address,
    _start_service,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2_grpc import (
    DiscoveryServiceStub,
)
from ni_measurementlink_service.measurement.info import MeasurementInfo, ServiceInfo
from tests.utilities.fake_discovery_service import FakeDiscoveryServiceStub

_PROVIDED_MEASUREMENT_SERVICES = [
    "ni.measurementlink.measurement.v1.MeasurementService",
    "ni.measurementlink.measurement.v2.MeasurementService",
]

_PROVIDED_ANNOTATIONS = {
    "ni/service.description": "This annotation is just an example for this test",
    "ni/service.collection": "CurrentTests.Inrush",
    "ni/service.tags": '["NI_Example","Voltage"]',
    "client/extra.NumberID": "500",
    "client/extra.Parts": '["PartNumber_25898","PartNumber_25412"]',
}


_TEST_SERVICE_PORT = "9999"
_TEST_SERVICE_INFO = ServiceInfo(
    "TestServiceClass", "TestUrl", _PROVIDED_MEASUREMENT_SERVICES, _PROVIDED_ANNOTATIONS
)
_TEST_MEASUREMENT_INFO = MeasurementInfo(
    display_name="TestMeasurement",
    version="1.0.0.0",
    ui_file_paths=[],
)

_MOCK_KEY_FILE_CONTENT = {"SecurePort": "", "InsecurePort": _TEST_SERVICE_PORT}
_MOCK_REGISTRATION_FILE_CONTENT = {
    "discovery": {"path": "Discovery/NationalInstruments.MeasurementLink.DiscoveryService.exe"}
}


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


def test___get_discovery_service_address___start_service_jit___returns_expected_value(
    mocker: MockerFixture,
    temp_discovery_key_file_path: pathlib.Path,
    temp_registration_json_file_path: pathlib.Path,
    temp_directory: pathlib.Path,
):
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._get_key_file_path",
        return_value=temp_discovery_key_file_path,
    )
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._service_already_running",
        return_value=False,
    )
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._get_registration_json_file_path",
        return_value=temp_registration_json_file_path,
    )
    mock_popen = mocker.patch("subprocess.Popen")

    discovery_service_address = _get_discovery_service_address()

    exe_file_path = temp_directory / _MOCK_REGISTRATION_FILE_CONTENT["discovery"]["path"]

    mock_popen.assert_called_once_with([exe_file_path], cwd=exe_file_path.parent)
    assert _TEST_SERVICE_PORT in discovery_service_address


def test___get_discovery_service_address___key_file_not_exist___throws_timeouterror(
    mocker: MockerFixture,
    temp_discovery_key_file_path: pathlib.Path,
    temp_registration_json_file_path: pathlib.Path,
):
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._get_key_file_path",
        return_value=temp_discovery_key_file_path,
    )
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._START_SERVICE_TIMEOUT", 5.0
    )
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._open_key_file", side_effect=IOError
    )
    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._get_registration_json_file_path",
        return_value=temp_registration_json_file_path,
    )
    mocker.patch("subprocess.Popen")

    with pytest.raises(IOError) as exc_info:
        _get_discovery_service_address()
    assert exc_info.type is TimeoutError


def test___start_discovery_service___key_file_exist_after_poll___service_start_success(
    mocker: MockerFixture, temp_directory: pathlib.Path, temp_discovery_key_file_path: pathlib.Path
):
    exe_file_path = temp_directory / _MOCK_REGISTRATION_FILE_CONTENT["discovery"]["path"]

    mocker.patch(
        "ni_measurementlink_service._internal.discovery_client._open_key_file",
        side_effect=[IOError, IOError, IOError, temp_discovery_key_file_path],
    )
    mock_popen = mocker.patch("subprocess.Popen")

    _start_service(exe_file_path, temp_discovery_key_file_path)

    mock_popen.assert_called_once_with([exe_file_path], cwd=exe_file_path.parent)


@pytest.fixture
def discovery_client(discovery_service_stub: FakeDiscoveryServiceStub) -> DiscoveryClient:
    """Create a DiscoveryClient."""
    return DiscoveryClient(cast(DiscoveryServiceStub, discovery_service_stub))


@pytest.fixture
def discovery_service_stub() -> FakeDiscoveryServiceStub:
    """Create a FakeDiscoveryServiceStub."""
    return FakeDiscoveryServiceStub()


@pytest.fixture
def temp_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a temp directory to store discovery service key and registration files."""
    discovery_service_temp_path = tmp_path / "disc_temp"
    discovery_service_temp_path.mkdir()
    return discovery_service_temp_path


@pytest.fixture
def temp_discovery_key_file_path(temp_directory: pathlib.Path) -> pathlib.Path:
    """Create a discovery service key file."""
    temp_discovery_key_file_path = temp_directory / "test_discovery_service.json"
    temp_discovery_key_file_path.write_text(json.dumps(_MOCK_KEY_FILE_CONTENT))
    return temp_discovery_key_file_path


@pytest.fixture
def temp_registration_json_file_path(
    temp_directory: pathlib.Path,
) -> pathlib.Path:
    """Create a discovery service registration json file."""
    temp_registration_json_file_path = temp_directory / "test_measurementlink_services.json"
    temp_registration_json_file_path.write_text(json.dumps(_MOCK_REGISTRATION_FILE_CONTENT))
    return temp_registration_json_file_path


def _validate_grpc_request(request):
    assert request.location.insecure_port == _TEST_SERVICE_PORT
    assert request.location.location == "localhost"
    assert request.service_description.service_class == _TEST_SERVICE_INFO.service_class
    assert request.service_description.description_url == _TEST_SERVICE_INFO.description_url
    assert request.service_description.display_name == _TEST_MEASUREMENT_INFO.display_name
    assert set(request.service_description.provided_interfaces) >= set(
        _PROVIDED_MEASUREMENT_SERVICES
    )
    assert request.service_description.annotations == _PROVIDED_ANNOTATIONS

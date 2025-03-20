"""Contains tests to validate the discovery_client.py."""

from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
from io import StringIO
from typing import Any, cast
from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._annotations import (
    SERVICE_PROGRAMMINGLANGUAGE_KEY,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2 import (
    EnumerateServicesRequest,
    EnumerateServicesResponse,
    RegisterServiceRequest,
    RegisterServiceResponse,
    ResolveServiceRequest,
    ResolveServiceWithInformationRequest,
    ResolveServiceWithInformationResponse,
    ServiceDescriptor as GrpcServiceDescriptor,
    ServiceLocation as GrpcServiceLocation,
    UnregisterServiceRequest,
    UnregisterServiceResponse,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2_grpc import (
    DiscoveryServiceStub,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient, ServiceLocation
from ni_measurement_plugin_sdk_service.discovery._support import (
    _get_discovery_service_address,
    _open_key_file,
    _start_service,
)
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.info import (
    MeasurementInfo,
    ServiceInfo,
)
from tests.utilities.fake_rpc_error import FakeRpcError

if sys.platform == "win32":
    import win32file

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
_TEST_SERVICE_SSL_PORT = "9998"

_TEST_SERVICE_LOCATION = ServiceLocation("localhost", _TEST_SERVICE_PORT, _TEST_SERVICE_SSL_PORT)
_TEST_SERVICE_LOCATION_WITHOUT_SSL = _TEST_SERVICE_LOCATION._replace(ssl_authenticated_port="")

_TEST_SERVICE_INFO = ServiceInfo(
    service_class="TestServiceClass",
    description_url="TestUrl",
    provided_interfaces=_PROVIDED_MEASUREMENT_SERVICES,
    annotations=_PROVIDED_ANNOTATIONS,
    display_name="TestMeasurement",
    versions=["2.0.2"],
)
_TEST_SERVICE_INFO_WITHOUT_DISPLAY_NAME = _TEST_SERVICE_INFO._replace(display_name="")

_TEST_MEASUREMENT_INFO = MeasurementInfo(
    display_name="TestMeasurement",
    version="1.0.0.0",
    ui_file_paths=[],
)

_MOCK_KEY_FILE_CONTENT = {"SecurePort": "", "InsecurePort": _TEST_SERVICE_PORT}
_MOCK_REGISTRATION_FILE_CONTENT = {"discovery": {"path": "Discovery/NI.Discovery.V1.Service.exe"}}


def test___service_not_registered___register_service___sends_request_and_returns_id(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.RegisterService.return_value = RegisterServiceResponse(
        registration_id="abcd"
    )

    registration_id = discovery_client.register_service(_TEST_SERVICE_INFO, _TEST_SERVICE_LOCATION)

    discovery_service_stub.RegisterService.assert_called_once()
    request: RegisterServiceRequest = discovery_service_stub.RegisterService.call_args.args[0]
    expected_service_info = copy.deepcopy(_TEST_SERVICE_INFO)
    expected_service_info.annotations[SERVICE_PROGRAMMINGLANGUAGE_KEY] = "Python"
    _assert_service_info_equal(expected_service_info, request.service_description)
    _assert_service_location_equal(_TEST_SERVICE_LOCATION, request.location)
    assert registration_id == "abcd"


def test___service_registered___unregister_service___sends_request(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.UnregisterService.return_value = UnregisterServiceResponse()

    unregistration_success_flag = discovery_client.unregister_service("abcd")

    discovery_service_stub.UnregisterService.assert_called_once()
    request: UnregisterServiceRequest = discovery_service_stub.UnregisterService.call_args.args[0]
    assert request.registration_id == "abcd"
    assert unregistration_success_flag


def test___service_registered___resolve_service_without_version___sends_request(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.ResolveService.return_value = GrpcServiceLocation(
        location=_TEST_SERVICE_LOCATION.location,
        insecure_port=_TEST_SERVICE_LOCATION.insecure_port,
        ssl_authenticated_port=_TEST_SERVICE_LOCATION.ssl_authenticated_port,
    )

    service_location = discovery_client.resolve_service(
        _TEST_SERVICE_INFO.provided_interfaces[0], _TEST_SERVICE_INFO.service_class
    )

    discovery_service_stub.ResolveService.assert_called_once()
    request: ResolveServiceRequest = discovery_service_stub.ResolveService.call_args.args[0]
    assert _TEST_SERVICE_INFO.provided_interfaces[0] == request.provided_interface
    assert _TEST_SERVICE_INFO.service_class == request.service_class
    _assert_service_location_equal(_TEST_SERVICE_LOCATION, service_location)


def test___service_registered___resolve_service_with_version___sends_request(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.ResolveService.return_value = GrpcServiceLocation(
        location=_TEST_SERVICE_LOCATION.location,
        insecure_port=_TEST_SERVICE_LOCATION.insecure_port,
        ssl_authenticated_port=_TEST_SERVICE_LOCATION.ssl_authenticated_port,
    )

    service_location = discovery_client.resolve_service(
        provided_interface=_TEST_SERVICE_INFO.provided_interfaces[0],
        service_class=_TEST_SERVICE_INFO.service_class,
        version=_TEST_SERVICE_INFO.versions[0],
    )

    discovery_service_stub.ResolveService.assert_called_once()
    request: ResolveServiceRequest = discovery_service_stub.ResolveService.call_args.args[0]
    assert _TEST_SERVICE_INFO.provided_interfaces[0] == request.provided_interface
    assert _TEST_SERVICE_INFO.service_class == request.service_class
    assert _TEST_SERVICE_INFO.versions[0] == request.version
    _assert_service_location_equal(_TEST_SERVICE_LOCATION, service_location)


def test___service_not_registered___resolve_service___raises_not_found_error(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.ResolveService.side_effect = FakeRpcError(
        grpc.StatusCode.NOT_FOUND, details="Service not found"
    )

    with pytest.raises(grpc.RpcError) as exc_info:
        _ = discovery_client.resolve_service(
            _TEST_SERVICE_INFO.provided_interfaces[0], _TEST_SERVICE_INFO.service_class
        )

    discovery_service_stub.ResolveService.assert_called_once()
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


def test___service_not_registered___register_measurement_service___sends_request_and_warns(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.RegisterService.return_value = RegisterServiceResponse(
        registration_id="abcd"
    )

    with pytest.deprecated_call():
        registration_success_flag = discovery_client.register_measurement_service(
            _TEST_SERVICE_PORT, _TEST_SERVICE_INFO_WITHOUT_DISPLAY_NAME, _TEST_MEASUREMENT_INFO
        )

    discovery_service_stub.RegisterService.assert_called_once()
    request = discovery_service_stub.RegisterService.call_args.args[0]
    expected_service_info = copy.deepcopy(_TEST_SERVICE_INFO)
    expected_service_info.annotations[SERVICE_PROGRAMMINGLANGUAGE_KEY] = "Python"
    _assert_service_info_equal(expected_service_info, request.service_description)
    _assert_service_location_equal(_TEST_SERVICE_LOCATION_WITHOUT_SSL, request.location)
    assert discovery_client._registration_id == "abcd"
    assert registration_success_flag


def test___service_registered___unregister_service_no_args___sends_request_and_returns_true(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.RegisterService.return_value = RegisterServiceResponse(
        registration_id="abcd"
    )
    discovery_service_stub.UnregisterService.return_value = UnregisterServiceResponse()
    with pytest.deprecated_call():
        discovery_client.register_measurement_service(
            _TEST_SERVICE_PORT, _TEST_SERVICE_INFO_WITHOUT_DISPLAY_NAME, _TEST_MEASUREMENT_INFO
        )

    unregistration_success_flag = discovery_client.unregister_service()

    discovery_service_stub.UnregisterService.assert_called_once()
    request = discovery_service_stub.UnregisterService.call_args.args[0]
    assert request.registration_id == "abcd"
    assert unregistration_success_flag


def test___service_not_registered___unregister_service_no_args___only_returns_false(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    unregistration_success_flag = discovery_client.unregister_service()

    discovery_service_stub.UnregisterService.assert_not_called()
    assert not unregistration_success_flag


def test___discovery_service_not_running___get_discovery_service_address___starts_discovery_service(
    mocker: MockerFixture,
    temp_discovery_key_file_path: pathlib.Path,
    temp_registration_json_file_path: pathlib.Path,
    temp_directory: pathlib.Path,
    subprocess_popen_kwargs: dict[str, Any],
):
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_key_file_path",
        return_value=temp_discovery_key_file_path,
    )
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._service_already_running",
        return_value=False,
    )
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_registration_json_file_path",
        return_value=temp_registration_json_file_path,
    )
    mock_popen = mocker.patch("subprocess.Popen")

    discovery_service_address = _get_discovery_service_address()

    exe_file_path = temp_directory / _MOCK_REGISTRATION_FILE_CONTENT["discovery"]["path"]

    mock_popen.assert_called_once_with(
        [exe_file_path],
        cwd=exe_file_path.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **subprocess_popen_kwargs,
    )
    assert _TEST_SERVICE_PORT in discovery_service_address


def test___key_file_never_created___get_discovery_service_address___throws_timeout_error(
    mocker: MockerFixture,
    temp_discovery_key_file_path: pathlib.Path,
    temp_registration_json_file_path: pathlib.Path,
):
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_key_file_path",
        return_value=temp_discovery_key_file_path,
    )
    mocker.patch("ni_measurement_plugin_sdk_service.discovery._support._START_SERVICE_TIMEOUT", 5.0)
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._open_key_file", side_effect=OSError
    )
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_registration_json_file_path",
        return_value=temp_registration_json_file_path,
    )
    mocker.patch("subprocess.Popen")

    with pytest.raises(OSError) as exc_info:
        _get_discovery_service_address()
    assert exc_info.type is TimeoutError


@pytest.mark.parametrize(
    "windows_error_code", [2, 3]
)  # ERROR_FILE_NOT_FOUND = 2, ERROR_PATH_NOT_FOUND = 3
def test___key_file_not_exist___open_key_file___raises_file_not_found_error(
    mocker: MockerFixture, temp_discovery_key_file_path: pathlib.Path, windows_error_code: int
) -> None:
    if sys.platform != "win32":
        pytest.skip("Windows-only test")
    else:
        mocker.patch(
            "win32file.CreateFile",
            side_effect=win32file.error(windows_error_code, "CreateFileA", "File not found"),
        )

        with pytest.raises(FileNotFoundError):
            _open_key_file(str(temp_discovery_key_file_path))


def test___key_file_exist_after_poll___start_discovery_service___discovery_service_started(
    mocker: MockerFixture,
    temp_directory: pathlib.Path,
    temp_discovery_key_file_path: pathlib.Path,
    subprocess_popen_kwargs: dict[str, Any],
):
    exe_file_path = temp_directory / _MOCK_REGISTRATION_FILE_CONTENT["discovery"]["path"]

    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._open_key_file",
        side_effect=[OSError, OSError, OSError, StringIO()],
    )
    mock_popen = mocker.patch("subprocess.Popen")

    _start_service(exe_file_path, temp_discovery_key_file_path)

    mock_popen.assert_called_once_with(
        [exe_file_path],
        cwd=exe_file_path.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **subprocess_popen_kwargs,
    )


def test___discovery_service_exe_unavailable___register_service___raises_file_not_found_error(
    mocker: MockerFixture,
    temp_discovery_key_file_path: pathlib.Path,
    temp_registration_json_file_path: pathlib.Path,
):
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_key_file_path",
        return_value=temp_discovery_key_file_path,
    )
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._support._get_registration_json_file_path",
        return_value=temp_registration_json_file_path,
    )
    mocker.patch("subprocess.Popen", side_effect=FileNotFoundError)
    discovery_client = DiscoveryClient()

    with pytest.raises(FileNotFoundError):
        discovery_client.register_service(_TEST_SERVICE_INFO, _TEST_SERVICE_LOCATION)


@pytest.mark.parametrize("programming_language", ["Python", "LabVIEW"])
def test___registered_measurements___enumerate_services___returns_list_of_measurements(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock, programming_language: str
):
    expected_service_info = copy.deepcopy(_TEST_SERVICE_INFO)
    expected_service_info.annotations[SERVICE_PROGRAMMINGLANGUAGE_KEY] = programming_language
    discovery_service_stub.EnumerateServices.return_value = EnumerateServicesResponse(
        available_services=[
            GrpcServiceDescriptor(
                display_name=expected_service_info.display_name,
                description_url=expected_service_info.description_url,
                provided_interfaces=expected_service_info.provided_interfaces,
                annotations=expected_service_info.annotations,
                service_class=expected_service_info.service_class,
                versions=expected_service_info.versions,
            )
        ]
    )

    available_measurements = discovery_client.enumerate_services(
        _TEST_SERVICE_INFO.provided_interfaces[1]
    )

    discovery_service_stub.EnumerateServices.assert_called_once()
    request: EnumerateServicesRequest = discovery_service_stub.EnumerateServices.call_args.args[0]
    assert _TEST_SERVICE_INFO.provided_interfaces[1] == request.provided_interface
    for measurement in available_measurements:
        _assert_service_info_equal(expected_service_info, measurement)


def test___no_registered_measurements___enumerate_services___returns_empty_list(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.EnumerateServices.return_value = EnumerateServicesResponse()

    available_measurements = discovery_client.enumerate_services(
        _TEST_SERVICE_INFO.provided_interfaces[1]
    )

    discovery_service_stub.EnumerateServices.assert_called_once()
    request: EnumerateServicesRequest = discovery_service_stub.EnumerateServices.call_args.args[0]
    assert _TEST_SERVICE_INFO.provided_interfaces[1] == request.provided_interface
    assert not available_measurements


@pytest.mark.parametrize("programming_language", ["Python", "LabVIEW"])
def test___registered_measurements___resolve_service_with_information___sends_request(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock, programming_language: str
):
    expected_service_info = copy.deepcopy(_TEST_SERVICE_INFO)
    expected_service_info.annotations[SERVICE_PROGRAMMINGLANGUAGE_KEY] = programming_language
    discovery_service_stub.ResolveServiceWithInformation.return_value = (
        ResolveServiceWithInformationResponse(
            service_location=GrpcServiceLocation(
                location=_TEST_SERVICE_LOCATION.location,
                insecure_port=_TEST_SERVICE_LOCATION.insecure_port,
                ssl_authenticated_port=_TEST_SERVICE_LOCATION.ssl_authenticated_port,
            ),
            service_descriptor=GrpcServiceDescriptor(
                display_name=expected_service_info.display_name,
                description_url=expected_service_info.description_url,
                provided_interfaces=expected_service_info.provided_interfaces,
                annotations=expected_service_info.annotations,
                service_class=expected_service_info.service_class,
                versions=expected_service_info.versions,
            ),
        )
    )

    service_location, service_info = discovery_client.resolve_service_with_information(
        provided_interface=_TEST_SERVICE_INFO.provided_interfaces[0],
        service_class=_TEST_SERVICE_INFO.service_class,
        version=_TEST_SERVICE_INFO.versions[0],
    )

    discovery_service_stub.ResolveServiceWithInformation.assert_called_once()
    request: ResolveServiceWithInformationRequest = (
        discovery_service_stub.ResolveServiceWithInformation.call_args.args[0]
    )
    assert _TEST_SERVICE_INFO.provided_interfaces[0] == request.provided_interface
    assert _TEST_SERVICE_INFO.service_class == request.service_class
    assert _TEST_SERVICE_INFO.versions[0] == request.version
    _assert_service_location_equal(_TEST_SERVICE_LOCATION, service_location)
    _assert_service_info_equal(expected_service_info, service_info)


def test___no_registered_measurements___resolve_service_with_information___raises_not_found_error(
    discovery_client: DiscoveryClient, discovery_service_stub: Mock
):
    discovery_service_stub.ResolveServiceWithInformation.side_effect = FakeRpcError(
        grpc.StatusCode.NOT_FOUND, details="Service not found"
    )

    with pytest.raises(grpc.RpcError) as exc_info:
        _ = discovery_client.resolve_service_with_information(
            provided_interface=_TEST_SERVICE_INFO.provided_interfaces[0],
            service_class=_TEST_SERVICE_INFO.service_class,
            version=_TEST_SERVICE_INFO.versions[0],
        )

    discovery_service_stub.ResolveServiceWithInformation.assert_called_once()
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.fixture(scope="module")
def subprocess_popen_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.DETACHED_PROCESS
    return kwargs


@pytest.fixture
def discovery_client(
    discovery_service_stub: Mock, grpc_channel_pool: Mock, mocker: MockerFixture
) -> DiscoveryClient:
    """Create a DiscoveryClient."""
    mocker.patch(
        "ni_measurement_plugin_sdk_service.discovery._client.DiscoveryClient._get_stub",
        return_value=discovery_service_stub,
    )
    return DiscoveryClient(grpc_channel_pool=cast(GrpcChannelPool, grpc_channel_pool))


@pytest.fixture
def discovery_service_stub(mocker: MockerFixture) -> Mock:
    """Create a mock DiscoveryServiceStub."""
    stub = mocker.create_autospec(DiscoveryServiceStub)
    stub.RegisterService = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.UnregisterService = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.EnumerateServices = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.ResolveService = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    stub.ResolveServiceWithInformation = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    return stub


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


def _assert_service_location_equal(
    expected: ServiceLocation, actual: ServiceLocation | GrpcServiceLocation
) -> None:
    assert expected.location == actual.location
    assert expected.insecure_port == actual.insecure_port
    assert expected.ssl_authenticated_port == actual.ssl_authenticated_port


def _assert_service_info_equal(
    expected: ServiceInfo, actual: ServiceInfo | GrpcServiceDescriptor
) -> None:
    assert expected.display_name == actual.display_name
    assert expected.description_url == actual.description_url
    assert set(expected.provided_interfaces) == set(actual.provided_interfaces)
    assert expected.service_class == actual.service_class
    assert expected.annotations == actual.annotations
    assert expected.versions == actual.versions

from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._drivers._grpcdevice import (
    SERVICE_CLASS,
    get_grpc_device_server_location,
    get_insecure_grpc_device_server_channel,
)
from ni_measurement_plugin_sdk_service.discovery import ServiceLocation
from tests.utilities import fake_driver


def test___default_configuration___get_grpc_device_server_location___resolves_service_and_returns_discovered_location(
    discovery_client: Mock,
) -> None:
    discovery_client.resolve_service.return_value = ServiceLocation("localhost", "1234", "")

    service_location = get_grpc_device_server_location(
        discovery_client, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    discovery_client.resolve_service.assert_called_with(
        provided_interface=fake_driver.GRPC_SERVICE_INTERFACE_NAME,
        service_class=SERVICE_CLASS,
    )
    assert service_location == ServiceLocation("localhost", "1234", "")


def test___use_grpc_device_server_false___get_grpc_device_server_location___returns_empty_string(
    discovery_client: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._grpcdevice.USE_GRPC_DEVICE_SERVER", False
    )

    service_location = get_grpc_device_server_location(
        discovery_client, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    assert service_location is None


@pytest.mark.parametrize(
    "grpc_device_server_address,expected_location",
    [
        ("http://[::1]:31763", ServiceLocation("[::1]", "31763", "")),
        ("http://localhost:1234", ServiceLocation("localhost", "1234", "")),
        ("http://somehost:31763/", ServiceLocation("somehost", "31763", "")),
        ("https://somehost:31763/", ServiceLocation("somehost", "", "31763")),
    ],
)
def test___grpc_device_server_address_set___get_grpc_device_server_location___returns_configured_address(
    discovery_client: Mock,
    mocker: MockerFixture,
    grpc_device_server_address: str,
    expected_location: ServiceLocation,
) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._grpcdevice.GRPC_DEVICE_SERVER_ADDRESS",
        grpc_device_server_address,
    )

    service_location = get_grpc_device_server_location(
        discovery_client, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    assert service_location == expected_location


@pytest.mark.parametrize(
    "grpc_device_server_address,expected_message",
    [
        (
            "file:///c:/windows/system.ini",
            "Unsupported URL scheme 'file' in 'file:///c:/windows/system.ini'",
        ),
        (
            "http://localhost:1234/index.html",
            "Unsupported path '/index.html' in 'http://localhost:1234/index.html'",
        ),
        (
            "http://localhost:1234/;param=123",
            "Unsupported path '/;param=123' in 'http://localhost:1234/;param=123'",
        ),
        (
            "http://localhost:1234?query=123",
            "Unsupported query '?query=123' in 'http://localhost:1234?query=123'",
        ),
        (
            "http://localhost:1234#fragment",
            "Unsupported fragment '#fragment' in 'http://localhost:1234#fragment'",
        ),
        (
            "http://:1234",
            "No host specified in 'http://:1234'",
        ),
        (
            "http://localhost",
            "No port number specified in 'http://localhost'",
        ),
    ],
)
def test___grpc_device_server_address_unsupported___get_grpc_device_server_location___raises_value_error(
    discovery_client: Mock,
    mocker: MockerFixture,
    grpc_device_server_address: str,
    expected_message: str,
) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._grpcdevice.GRPC_DEVICE_SERVER_ADDRESS",
        grpc_device_server_address,
    )

    with pytest.raises(ValueError) as exc_info:
        _ = get_grpc_device_server_location(
            discovery_client, fake_driver.GRPC_SERVICE_INTERFACE_NAME
        )

    assert exc_info.value.args[0] == expected_message


def test___default_configuration___get_insecure_grpc_device_server_channel___resolves_service_and_returns_channel_with_configured_address(
    discovery_client: Mock,
    grpc_channel: Mock,
    grpc_channel_pool: Mock,
) -> None:
    discovery_client.resolve_service.return_value = ServiceLocation("localhost", "1234", "")
    grpc_channel_pool.get_channel.return_value = grpc_channel

    returned_channel = get_insecure_grpc_device_server_channel(
        discovery_client, grpc_channel_pool, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    discovery_client.resolve_service.assert_called_with(
        provided_interface=fake_driver.GRPC_SERVICE_INTERFACE_NAME,
        service_class=SERVICE_CLASS,
    )
    grpc_channel_pool.get_channel.assert_called_with("localhost:1234")
    assert returned_channel is grpc_channel


def test___use_grpc_device_server_false___get_insecure_grpc_device_server_channel___returns_none(
    discovery_client: Mock,
    grpc_channel_pool: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._grpcdevice.USE_GRPC_DEVICE_SERVER", False
    )

    returned_channel = get_insecure_grpc_device_server_channel(
        discovery_client, grpc_channel_pool, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    assert returned_channel is None


def test___grpc_device_server_address_set___get_insecure_grpc_device_server_channel___returns_channel_with_configured_address(
    discovery_client: Mock,
    grpc_channel: Mock,
    grpc_channel_pool: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "ni_measurement_plugin_sdk_service._drivers._grpcdevice.GRPC_DEVICE_SERVER_ADDRESS",
        "http://[::1]:31763",
    )
    grpc_channel_pool.get_channel.return_value = grpc_channel

    returned_channel = get_insecure_grpc_device_server_channel(
        discovery_client, grpc_channel_pool, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    grpc_channel_pool.get_channel.assert_called_with("[::1]:31763")
    assert returned_channel is grpc_channel

from unittest.mock import Mock

from pytest_mock import MockerFixture

from ni_measurementlink_service._drivers._grpcdevice import (
    SERVICE_CLASS,
    get_insecure_grpc_device_server_channel,
)
from ni_measurementlink_service.discovery import ServiceLocation
from tests.utilities import fake_driver


def test___default_configuration___get_insecure_grpc_device_server_channel___returns_discovered_channel(
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
    mocker.patch("ni_measurementlink_service._drivers._grpcdevice.USE_GRPC_DEVICE_SERVER", False)

    returned_channel = get_insecure_grpc_device_server_channel(
        discovery_client, grpc_channel_pool, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    assert returned_channel is None


def test___grpc_device_server_address_set___get_insecure_grpc_device_server_channel___returns_configured_channel(
    discovery_client: Mock,
    grpc_channel: Mock,
    grpc_channel_pool: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "ni_measurementlink_service._drivers._grpcdevice.GRPC_DEVICE_SERVER_ADDRESS",
        "http://[::1]:31763",
    )
    grpc_channel_pool.get_channel.return_value = grpc_channel

    returned_channel = get_insecure_grpc_device_server_channel(
        discovery_client, grpc_channel_pool, fake_driver.GRPC_SERVICE_INTERFACE_NAME
    )

    discovery_client.resolve_service.assert_not_called()
    grpc_channel_pool.get_channel.assert_called_with("[::1]:31763")
    assert returned_channel is grpc_channel

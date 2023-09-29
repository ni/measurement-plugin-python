from unittest.mock import Mock

import pytest

from ni_measurementlink_service._drivers._grpcdevice import (
    SERVICE_CLASS,
    get_insecure_grpc_device_channel,
)
from ni_measurementlink_service._internal.discovery_client import ServiceLocation
from tests.utilities import fake_driver


def test___valid_driver_module___get_insecure_grpc_device_channel____returns_channel(
    discovery_client: Mock,
    grpc_channel: Mock,
    grpc_channel_pool: Mock,
) -> None:
    discovery_client.resolve_service.return_value = ServiceLocation("localhost", "1234", "")
    grpc_channel_pool.get_channel.return_value = grpc_channel

    returned_channel = get_insecure_grpc_device_channel(
        discovery_client, grpc_channel_pool, fake_driver
    )

    discovery_client.resolve_service.assert_called_with(
        provided_interface=fake_driver.GRPC_SERVICE_INTERFACE_NAME,
        service_class=SERVICE_CLASS,
    )
    grpc_channel_pool.get_channel.assert_called_with("localhost:1234")
    assert returned_channel is grpc_channel


def test___invalid_driver_module___get_insecure_grpc_device_channel____raises_type_error(
    discovery_client: Mock,
    grpc_channel_pool: Mock,
) -> None:
    discovery_client.resolve_service.return_value = ServiceLocation("localhost", "1234", "")

    with pytest.raises(TypeError):
        _ = get_insecure_grpc_device_channel(discovery_client, grpc_channel_pool, pytest)  # type: ignore[arg-type]

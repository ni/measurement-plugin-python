"""Contains tests to validate the pin_map_client.py.
"""

import pathlib
from typing import cast
from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.pinmap.v1.pin_map_service_pb2 import (
    PinMap,
    UpdatePinMapFromXmlRequest,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.pinmap.v1.pin_map_service_pb2_grpc import (
    PinMapServiceStub,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.pin_map._client import PinMapClient


def test__valid_pin_map_file__register_pin_map___sends_request_and_returns_id(
    pin_map_client: PinMapClient,
    pin_map_stub: Mock,
    pin_map_directory: pathlib.Path,
) -> None:
    pin_map_path = str(pin_map_directory / "1Smu1ChannelGroup1Pin1Site.pinmap")
    pin_map_stub.UpdatePinMapFromXml.return_value = PinMap(pin_map_id=pin_map_path)

    registered_pin_map_id = pin_map_client.update_pin_map(pin_map_path)

    pin_map_stub.UpdatePinMapFromXml.assert_called_once()
    request: UpdatePinMapFromXmlRequest = pin_map_stub.UpdatePinMapFromXml.call_args.args[0]
    assert request.pin_map_id == pin_map_path
    assert request.pin_map_xml == _get_pin_map_file_contents(pin_map_path)
    assert registered_pin_map_id == pin_map_path


def test__invalid_pin_map_file_path__register_pin_map___raises_file_not_found_error(
    pin_map_client: PinMapClient,
) -> None:
    pin_map_path = "InvalidPinmap.pinmap"

    with pytest.raises(FileNotFoundError):
        _ = pin_map_client.update_pin_map(pin_map_path)


def _get_pin_map_file_contents(pin_map_path: str) -> str:
    with open(pin_map_path, "r", encoding="utf-8-sig") as file:
        xml_content = file.read()
    return xml_content


@pytest.fixture
def pin_map_client(
    discovery_client: Mock,
    grpc_channel_pool: Mock,
    mocker: MockerFixture,
    pin_map_stub: Mock,
) -> PinMapClient:
    """Create a Client with a mock PinMapServiceStub."""
    mocker.patch(
        "ni_measurement_plugin_sdk_service.pin_map.PinMapClient._get_stub",
        return_value=pin_map_stub,
    )
    client = PinMapClient(
        discovery_client=cast(DiscoveryClient, discovery_client),
        grpc_channel_pool=cast(GrpcChannelPool, grpc_channel_pool),
    )
    return client


@pytest.fixture
def pin_map_stub(mocker: MockerFixture) -> Mock:
    """Create a mock PinMapServiceStub."""
    stub = mocker.create_autospec(PinMapServiceStub)
    stub.UpdatePinMapFromXml = mocker.create_autospec(grpc.UnaryUnaryMultiCallable)
    return stub

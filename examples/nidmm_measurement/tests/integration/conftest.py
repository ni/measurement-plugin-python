"""Integration test fixtures for NI-DMM measurements."""
from typing import Generator

import grpc
import measurement
import pytest
from _helpers import PinMapClient

from ni_measurementlink_service._internal.discovery_client import DiscoveryClient
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2_grpc import (
    MeasurementServiceStub,
)
from ni_measurementlink_service.measurement.service import MeasurementService


@pytest.fixture
def discovery_client() -> DiscoveryClient:
    """Test fixture that creates a DiscoveryClient."""
    return DiscoveryClient()


@pytest.fixture
def measurement_grpc_channel(
    measurement_service: MeasurementService,
) -> Generator[grpc.Channel, None, None]:
    """Test fixture that creates a gRPC channel."""
    target = f"localhost:{measurement_service.grpc_service.port}"
    options = [
        ("grpc.max_receive_message_length", -1),
        ("grpc.max_send_message_length", -1),
    ]
    with grpc.insecure_channel(target, options) as channel:
        yield channel


@pytest.fixture
def measurement_service() -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def measurement_stub(measurement_grpc_channel: grpc.Channel) -> MeasurementServiceStub:
    """Test fixture that creates a MeasurementService v2 stub."""
    return MeasurementServiceStub(measurement_grpc_channel)


@pytest.fixture
def pin_map_client(discovery_client: DiscoveryClient) -> PinMapClient:
    """Test fixture that creates a PinMapClient."""
    location = discovery_client.resolve_service(
        provided_interface="ni.measurementlink.pinmap.v1.PinMapService",
        service_class="ni.measurementlink.pinmap.v1.PinMapService",
    )
    channel = grpc.insecure_channel(location.insecure_address)
    return PinMapClient(grpc_channel=channel)


@pytest.fixture
def pin_map_id(pin_map_client: PinMapClient) -> str:
    """Test fixture that registers the pin map and returns its id."""
    return pin_map_client.update_pin_map("NIDmmMeasurement.pinmap")

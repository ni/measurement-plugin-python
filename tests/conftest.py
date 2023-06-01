"""Pytest configuration file."""
import pathlib
from typing import Generator

import grpc
import pytest

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2 as v1_measurement_service_pb2,
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import MeasurementService


@pytest.fixture(scope="module")
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "assets"


@pytest.fixture
def grpc_channel(measurement_service: MeasurementService) -> Generator[grpc.Channel, None, None]:
    """Test fixture that creates a gRPC channel."""
    target = f"localhost:{measurement_service.grpc_service.port}"
    options = [
        ("grpc.max_receive_message_length", -1),
        ("grpc.max_send_message_length", -1),
    ]
    with grpc.insecure_channel(target, options) as channel:
        yield channel


@pytest.fixture
def stub_v1(grpc_channel: grpc.Channel) -> v1_measurement_service_pb2_grpc.MeasurementServiceStub:
    """Test fixture that creates a MeasurementService v1 stub."""
    return v1_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)


@pytest.fixture
def stub_v2(grpc_channel: grpc.Channel) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    """Test fixture that creates a MeasurementService v2 stub."""
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)

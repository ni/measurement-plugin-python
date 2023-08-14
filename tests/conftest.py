"""Pytest configuration file."""
import pathlib
import sys
from typing import Generator

import grpc
import pytest

from ni_measurementlink_service._internal.discovery_client import _get_registration_json_file_path
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import MeasurementService
from tests.utilities.discovery_service_process import DiscoveryServiceProcess


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


@pytest.fixture(scope="session")
def discovery_service_process() -> Generator[DiscoveryServiceProcess, None, None]:
    """Test fixture that creates discovery service process."""
    if sys.platform != "win32":
        pytest.skip(
            f"Platform {sys.platform} is not supported for starting discovery service."
            "Could not proceed to run the tests."
        )
    elif not _get_registration_json_file_path().exists():
        pytest.skip(
            "MeasurementLink registration file not found or MeasurementLink not installed."
            "Could not proceed to run the tests. Install MeasurementLink to create the registration file."
        )
    else:
        with DiscoveryServiceProcess() as proc:
            yield proc

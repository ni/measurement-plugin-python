"""Shared fixtures for ni-measurement-plugin-sdk-generator tests."""

import pathlib
import sys
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service.discovery._support import _get_registration_json_file_path
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import test_measurement


@pytest.fixture
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "test_assets"


@pytest.fixture(scope="session")
def discovery_service_process() -> Generator[DiscoveryServiceProcess, None, None]:
    """Test fixture that creates discovery service process."""
    if sys.platform != "win32":
        pytest.skip(f"Platform {sys.platform} is not supported for discovery service tests.")

    try:
        registration_json_file_exists = _get_registration_json_file_path().exists()
    except FileNotFoundError:  # registry key not found
        registration_json_file_exists = False
    if not registration_json_file_exists:
        pytest.skip("Registration file not found. Ensure the Measurement Plug-In SDK is installed.")

    with DiscoveryServiceProcess() as proc:
        yield proc


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: Generator[DiscoveryServiceProcess, None, None]
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement plug-in service."""
    with test_measurement.measurement_service.host_service() as service:
        yield service

"""Shared fixtures for ni-measurement-plugin-sdk-generator tests."""

from __future__ import annotations

import functools
import pathlib
import sys
from collections.abc import Generator, Sequence
from typing import Protocol

import pytest
from click.testing import CliRunner, Result
from ni_measurement_plugin_sdk_service.discovery._support import (
    _get_registration_json_file_path,
)

import ni_measurement_plugin_sdk_generator.client as client_generator
import ni_measurement_plugin_sdk_generator.plugin as plugin_generator
from tests.utilities.discovery_service_process import DiscoveryServiceProcess


class CliRunnerFunction(Protocol):
    """Protocol for a callable that executes a CLI command using Click's CliRunner."""

    def __call__(self, args: Sequence[str], input: str | None = None) -> Result:
        """Execute the CLI command with the provided arguments."""


@pytest.fixture
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "test_assets"


@pytest.fixture(scope="session")
def discovery_service_process() -> Generator[DiscoveryServiceProcess]:
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


@pytest.fixture
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "pin_map"


@pytest.fixture(scope="session")
def create_client() -> Generator[CliRunnerFunction]:
    """Test fixture for calling client generator cli."""
    runner = CliRunner(mix_stderr=False)
    yield functools.partial(runner.invoke, client_generator.create_client, standalone_mode=False)


@pytest.fixture(scope="session")
def create_measurement() -> Generator[CliRunnerFunction]:
    """Test fixture for calling plugin generator cli."""
    runner = CliRunner(mix_stderr=False)
    yield functools.partial(
        runner.invoke, plugin_generator.create_measurement, standalone_mode=False
    )

"""Pytest configuration file for acceptance tests."""

import pathlib
import warnings
from collections.abc import Generator

import pytest

from ni_measurement_plugin_sdk_service.measurement import WrongMessageTypeWarning


@pytest.fixture(scope="module")
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "acceptance" / "session_management"


@pytest.fixture
def filter_wrong_configurations_message_type_warnings() -> Generator:
    """Test fixture to filter out WrongMessageTypeWarning warnings for Configurations messages."""
    warnings.filterwarnings("ignore", ".*Configurations.*", WrongMessageTypeWarning)
    yield

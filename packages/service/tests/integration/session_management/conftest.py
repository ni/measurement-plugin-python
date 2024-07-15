"""Pytest configuration file for integration tests."""

import pathlib

import pytest


@pytest.fixture(scope="module")
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "integration" / "session_management"

"""Shared fixtures for ni-measurement-generator tests."""

import pathlib

import pytest


@pytest.fixture
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "test_assets"

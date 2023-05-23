"""Pytest configuration file."""
import pathlib

import pytest


@pytest.fixture(scope="module")
def test_assets_directory() -> pathlib.Path:
    """Gets path to test_assets directory."""
    return pathlib.Path(__file__).parent / "assets"

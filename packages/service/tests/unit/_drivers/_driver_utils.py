"""Driver-related unit test utilities."""

from __future__ import annotations

from typing import TypeVar
from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service._configuration import MIDriverOptions

TSession = TypeVar("TSession")


def create_mock_session(session_type: type[TSession]) -> Mock:
    """Create a single mock session object."""
    mock = create_autospec(session_type)
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


def create_mock_sessions(session_type: type[TSession], count: int) -> list[Mock]:
    """Create multiple mock session objects."""
    return [create_mock_session(session_type) for _ in range(count)]


def set_simulation_options(
    driver_name: str, mocker: MockerFixture, simulate: bool, board_type: str, model: str
) -> None:
    """Set simulation options for the specified driver."""
    mocker.patch(
        f"ni_measurement_plugin_sdk_service._drivers._{driver_name}.{driver_name.upper()}_OPTIONS",
        MIDriverOptions(driver_name, simulate, board_type, model),
    )

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ni_measurement_plugin_sdk_service.measurement.service import MeasurementContext

pytestmark = pytest.mark.usefixtures("measurement_service_context")


def test___single_pin___reserve_session___session_reserved(
    measurement_service_context: Mock,
    session_management_client: Mock,
    single_session_reservation: Mock,
) -> None:
    measurement_context = MeasurementContext()

    reservation = measurement_context.reserve_session("Pin1")

    session_management_client.reserve_session.assert_called_once_with(
        context=measurement_service_context.pin_map_context, pin_or_relay_names="Pin1", timeout=0.0
    )
    assert reservation is single_session_reservation


def test___multiple_pins___reserve_session___session_reserved(
    measurement_service_context: Mock,
    session_management_client: Mock,
    single_session_reservation: Mock,
) -> None:
    measurement_context = MeasurementContext()

    reservation = measurement_context.reserve_session(["Pin1", "Pin2"])

    session_management_client.reserve_session.assert_called_once_with(
        context=measurement_service_context.pin_map_context,
        pin_or_relay_names=["Pin1", "Pin2"],
        timeout=0.0,
    )
    assert reservation is single_session_reservation


@pytest.mark.parametrize("no_pins", ["", [], None])
def test___no_pins___reserve_session___value_error_raised(
    no_pins: str | list[str] | None,
) -> None:
    measurement_context = MeasurementContext()

    with pytest.raises(ValueError):
        _ = measurement_context.reserve_session(no_pins)  # type: ignore[arg-type]


def test___timeout___reserve_session___timeout_specified(
    measurement_service_context: Mock,
    session_management_client: Mock,
) -> None:
    measurement_context = MeasurementContext()

    _ = measurement_context.reserve_session("Pin1", 10.0)

    session_management_client.reserve_session.assert_called_once_with(
        context=measurement_service_context.pin_map_context, pin_or_relay_names="Pin1", timeout=10.0
    )


def test___single_pin___reserve_sessions___session_reserved(
    measurement_service_context: Mock,
    session_management_client: Mock,
    multi_session_reservation: Mock,
) -> None:
    measurement_context = MeasurementContext()

    reservation = measurement_context.reserve_sessions("Pin1")

    session_management_client.reserve_sessions.assert_called_once_with(
        context=measurement_service_context.pin_map_context, pin_or_relay_names="Pin1", timeout=0.0
    )
    assert reservation is multi_session_reservation


def test___multiple_pins___reserve_sessions___session_reserved(
    measurement_service_context: Mock,
    session_management_client: Mock,
    multi_session_reservation: Mock,
) -> None:
    measurement_context = MeasurementContext()

    reservation = measurement_context.reserve_sessions(["Pin1", "Pin2"])

    session_management_client.reserve_sessions.assert_called_once_with(
        context=measurement_service_context.pin_map_context,
        pin_or_relay_names=["Pin1", "Pin2"],
        timeout=0.0,
    )
    assert reservation is multi_session_reservation


@pytest.mark.parametrize("no_pins", ["", [], None])
def test___no_pins___reserve_sessions___value_error_raised(
    no_pins: str | list[str] | None,
) -> None:
    measurement_context = MeasurementContext()

    with pytest.raises(ValueError):
        _ = measurement_context.reserve_sessions(no_pins)  # type: ignore[arg-type]


def test___timeout___reserve_sessions___timeout_specified(
    measurement_service_context: Mock,
    session_management_client: Mock,
) -> None:
    measurement_context = MeasurementContext()

    _ = measurement_context.reserve_sessions("Pin1", 10.0)

    session_management_client.reserve_sessions.assert_called_once_with(
        context=measurement_service_context.pin_map_context, pin_or_relay_names="Pin1", timeout=10.0
    )

"""Public API for accessing the MeasurementLink session management service."""

from __future__ import annotations

import warnings
from typing import Any

from deprecation import DeprecatedWarning

from ni_measurementlink_service.session_management._client import (
    SessionManagementClient,
)
from ni_measurementlink_service.session_management._constants import (
    GRPC_SERVICE_CLASS,
    GRPC_SERVICE_INTERFACE_NAME,
    INSTRUMENT_TYPE_NI_DAQMX,
    INSTRUMENT_TYPE_NI_DCPOWER,
    INSTRUMENT_TYPE_NI_DIGITAL_PATTERN,
    INSTRUMENT_TYPE_NI_DMM,
    INSTRUMENT_TYPE_NI_FGEN,
    INSTRUMENT_TYPE_NI_HSDIO,
    INSTRUMENT_TYPE_NI_MODEL_BASED_INSTRUMENT,
    INSTRUMENT_TYPE_NI_RELAY_DRIVER,
    INSTRUMENT_TYPE_NI_RFMX,
    INSTRUMENT_TYPE_NI_RFPM,
    INSTRUMENT_TYPE_NI_RFSA,
    INSTRUMENT_TYPE_NI_RFSG,
    INSTRUMENT_TYPE_NI_SCOPE,
    INSTRUMENT_TYPE_NI_SWITCH_EXECUTIVE_VIRTUAL_DEVICE,
    INSTRUMENT_TYPE_NONE,
    SITE_SYSTEM_PINS,
)
from ni_measurementlink_service.session_management._reservation import (
    BaseReservation,
    MultiplexerSessionContainer,
    MultiSessionReservation,
    SingleSessionReservation,
)
from ni_measurementlink_service.session_management._types import (
    ChannelMapping,
    Connection,
    PinMapContext,
    MultiplexerSessionInformation,
    SessionInformation,
    SessionInitializationBehavior,
    TypedConnection,
    TypedConnectionWithMultiplexer,
    TypedMultiplexerSessionInformation,
    TypedSessionInformation,
)

__all__ = [
    "BaseReservation",
    "ChannelMapping",
    "Client",
    "Connection",
    "GRPC_SERVICE_CLASS",
    "GRPC_SERVICE_INTERFACE_NAME",
    "INSTRUMENT_TYPE_NI_DAQMX",
    "INSTRUMENT_TYPE_NI_DCPOWER",
    "INSTRUMENT_TYPE_NI_DIGITAL_PATTERN",
    "INSTRUMENT_TYPE_NI_DMM",
    "INSTRUMENT_TYPE_NI_FGEN",
    "INSTRUMENT_TYPE_NI_HSDIO",
    "INSTRUMENT_TYPE_NI_MODEL_BASED_INSTRUMENT",
    "INSTRUMENT_TYPE_NI_RELAY_DRIVER",
    "INSTRUMENT_TYPE_NI_RFMX",
    "INSTRUMENT_TYPE_NI_RFPM",
    "INSTRUMENT_TYPE_NI_RFSA",
    "INSTRUMENT_TYPE_NI_RFSG",
    "INSTRUMENT_TYPE_NI_SCOPE",
    "INSTRUMENT_TYPE_NI_SWITCH_EXECUTIVE_VIRTUAL_DEVICE",
    "INSTRUMENT_TYPE_NONE",
    "MultiSessionReservation",
    "PinMapContext",
    "MultiplexerSessionContainer",
    "MultiplexerSessionInformation",
    "SessionInformation",
    "SessionInitializationBehavior",
    "SessionManagementClient",
    "SingleSessionReservation",
    "SITE_SYSTEM_PINS",
    "TypedConnection",
    "TypedConnectionWithMultiplexer",
    "TypedMultiplexerSessionInformation",
    "TypedSessionInformation",
]


def __getattr__(name: str) -> Any:
    if name == "Reservation":
        warnings.warn(
            DeprecatedWarning(
                name,
                deprecated_in="1.1.0",
                removed_in=None,
                details="Use MultiSessionReservation instead.",
            ),
            stacklevel=2,
        )
        return MultiSessionReservation
    else:
        raise AttributeError(f"module {__name__} has no attribute {name}")


Client = SessionManagementClient
"""Alias for compatibility with code that uses session_management.Client."""

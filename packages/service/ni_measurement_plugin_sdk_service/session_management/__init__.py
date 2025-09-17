"""Compatibility API for accessing the NI Session Management Service.

The public API for accessing the NI Session Management Service has moved to the
:mod:`ni.measurementlink.sessionmanagement.v1.client` package.

The :mod:`ni_measurement_plugin_sdk_service.session_management` subpackage
provides compatibility with existing applications and will be deprecated in a
future release.
"""

from ni.measurementlink.sessionmanagement.v1.client import (
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
    BaseReservation,
    ChannelMapping,
    Connection,
    MultiplexerSessionContainer,
    MultiplexerSessionInformation,
    MultiSessionReservation,
    PinMapContext,
    SessionInformation,
    SessionInitializationBehavior,
    SessionManagementClient,
    SingleSessionReservation,
    TypedConnection,
    TypedConnectionWithMultiplexer,
    TypedMultiplexerSessionInformation,
    TypedSessionInformation,
)

__all__ = [
    "GRPC_SERVICE_CLASS",
    "GRPC_SERVICE_INTERFACE_NAME",
    "INSTRUMENT_TYPE_NONE",
    "INSTRUMENT_TYPE_NI_DCPOWER",
    "INSTRUMENT_TYPE_NI_HSDIO",
    "INSTRUMENT_TYPE_NI_RFSA",
    "INSTRUMENT_TYPE_NI_RFMX",
    "INSTRUMENT_TYPE_NI_RFSG",
    "INSTRUMENT_TYPE_NI_RFPM",
    "INSTRUMENT_TYPE_NI_DMM",
    "INSTRUMENT_TYPE_NI_DIGITAL_PATTERN",
    "INSTRUMENT_TYPE_NI_SCOPE",
    "INSTRUMENT_TYPE_NI_FGEN",
    "INSTRUMENT_TYPE_NI_DAQMX",
    "INSTRUMENT_TYPE_NI_RELAY_DRIVER",
    "INSTRUMENT_TYPE_NI_MODEL_BASED_INSTRUMENT",
    "INSTRUMENT_TYPE_NI_SWITCH_EXECUTIVE_VIRTUAL_DEVICE",
    "SITE_SYSTEM_PINS",
    "BaseReservation",
    "ChannelMapping",
    "Connection",
    "MultiplexerSessionInformation",
    "MultiplexerSessionContainer",
    "MultiSessionReservation",
    "PinMapContext",
    "SessionInformation",
    "SessionInitializationBehavior",
    "SessionManagementClient",
    "SingleSessionReservation",
    "TypedConnection",
    "TypedConnectionWithMultiplexer",
    "TypedMultiplexerSessionInformation",
    "TypedSessionInformation",
]

Client = SessionManagementClient
"""Alias for compatibility with code that uses session_management.Client."""

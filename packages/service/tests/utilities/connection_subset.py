"""Utility to create and construct connection subset."""

from __future__ import annotations

from typing import NamedTuple, TypeVar

from ni_measurement_plugin_sdk_service.session_management import (
    Connection,
    TypedConnection,
    TypedConnectionWithMultiplexer,
)

_T = TypeVar("_T")
_TMultiplexer = TypeVar("_TMultiplexer")


class ConnectionSubset(NamedTuple):
    """An object that holds a subset of connection data."""

    pin_or_relay_name: str
    site: int
    resource_name: str
    channel_name: str

    multiplexer_resource_name: str = ""
    multiplexer_route: str = ""


def get_connection_subset(connection: Connection | TypedConnection[_T]) -> ConnectionSubset:
    """Constructs and returns a ConnectionSubset object."""
    return ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.session_info.resource_name,
        connection.channel_name,
    )


def get_connection_subset_with_multiplexer(
    connection: Connection | TypedConnectionWithMultiplexer[_T, _TMultiplexer],
) -> ConnectionSubset:
    """Constructs and returns a ConnectionSubset object with multiplexer data."""
    return ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.session_info.resource_name,
        connection.channel_name,
        connection.multiplexer_resource_name,
        connection.multiplexer_route,
    )

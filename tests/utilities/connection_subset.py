"""Utility to create and construct connection subset."""
from typing import NamedTuple, TypeVar, Union

from ni_measurementlink_service.session_management import (
    Connection,
    TypedConnection,
)

_T = TypeVar("_T")


class ConnectionSubset(NamedTuple):
    """An object that holds a subset of connection data."""

    pin_or_relay_name: str
    site: int

    resource_name: str
    channel_name: str


def get_connection_subset(connection: Union[Connection, TypedConnection[_T]]) -> ConnectionSubset:
    """Constructs and returns a ConnectionSubset object."""
    return ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.session_info.resource_name,
        connection.channel_name,
    )

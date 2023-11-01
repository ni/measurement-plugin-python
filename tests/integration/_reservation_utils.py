"""Connection subset utility."""
from typing import NamedTuple, TypeVar, Union

from ni_measurementlink_service.session_management import (
    Connection,
    TypedConnection,
)

_T = TypeVar("_T")


class _ConnectionSubset(NamedTuple):
    pin_or_relay_name: str
    site: int

    resource_name: str
    channel_name: str


def _get_subset(connection: Union[Connection, TypedConnection[_T]]) -> _ConnectionSubset:
    return _ConnectionSubset(
        connection.pin_or_relay_name,
        connection.site,
        connection.session_info.resource_name,
        connection.channel_name,
    )

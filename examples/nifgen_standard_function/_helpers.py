"""Helper classes and functions for MeasurementLink examples."""

import logging
from typing import Dict, NamedTuple, TypeVar

import grpc


class ServiceOptions(NamedTuple):
    """Service options specified on the command line."""

    use_grpc_device: bool
    grpc_device_address: str


T = TypeVar("T")


def str_to_enum(mapping: Dict[str, T], value: str) -> T:
    try:
        return mapping[value]
    except KeyError as e:
        logging.error("Unsupported enum value %s", value)
        raise grpc.RpcError(
            grpc.StatusCode.INVALID_ARGUMENT,
            f'Unsupported enum value "{value}"',
        ) from e

import socket

import win32api

from ni_measurement_plugin_sdk_service.session_management._constants import (
    REGISTERED_HOSTNAME,
    REGISTERED_IPADDRESS,
    REGISTERED_USERNAME,
    RESERVED_HOSTNAME,
    RESERVED_IPADDRESS,
    RESERVED_USERNAME,
)


def get_machine_details() -> tuple[dict[str, str], dict[str, str]]:
    """Get the machine details for reserved and registered annotations."""
    hostname = _get_hostname()
    username = _get_username()
    ip_address = _get_ip_address(hostname)

    reserved = {
        RESERVED_HOSTNAME: hostname,
        RESERVED_USERNAME: username,
        RESERVED_IPADDRESS: ip_address,
    }

    registered = {
        REGISTERED_HOSTNAME: hostname,
        REGISTERED_USERNAME: username,
        REGISTERED_IPADDRESS: ip_address,
    }

    return reserved, registered


def remove_reservation_annotations(annotations: dict[str, str]) -> dict[str, str]:
    """Remove reserved annotations from the provided annotations."""
    reservation_keys = {
        RESERVED_HOSTNAME,
        RESERVED_USERNAME,
        RESERVED_IPADDRESS,
    }
    return {k: v for k, v in annotations.items() if k not in reservation_keys}


def _get_hostname() -> str:
    try:
        return win32api.GetComputerName()
    except Exception:
        return ""


def _get_username() -> str:
    try:
        return win32api.GetUserName()
    except Exception:
        return ""


def _get_ip_address(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return ""

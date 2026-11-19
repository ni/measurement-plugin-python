"""Support functions for the NI Discovery Service."""

from __future__ import annotations

import json
import logging
import os
import pathlib
import subprocess  # nosec: B404
import sys
import time
import typing
from typing import Any

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
)

if sys.platform == "win32":
    import msvcrt
    import winreg

    import win32con
    import win32file
    from win32com.shell import shell, shellcon

_logger = logging.getLogger(__name__)
# Save Popen object to avoid "ResourceWarning: subprocess N is still running"
_discovery_service_subprocess: subprocess.Popen | None = None

_START_SERVICE_TIMEOUT = 30.0
_START_SERVICE_POLLING_INTERVAL = 100e-3

_DISCOVERY_SERVICE_ADDRESS_ENV_VAR = "DISCOVERY_SERVICE_ADDRESS"
_DISCOVERY_SERVICE_ENV_VAR_PREFIX = "NIDiscovery_"
_DISCOVERY_SERVICE_CLUSTER_ID_ENV_VAR = "ClusterId"

# Discovery Service versions that run a per-user instance record the publishing process in every key
# file they write, including the machine-wide compatibility key file.
_KEY_FILE_PROCESS_ID_PROPERTY = "ProcessId"


def _get_discovery_service_address() -> str:
    """Gets the address of the Discovery Service, starting it if necessary.

    The Discovery Service is resolved in this order:

    1. The ``DISCOVERY_SERVICE_ADDRESS`` environment variable, which the Discovery Service sets
       for the services it launches.
    2. The key file for the cluster selected by the ``NIDiscovery_ClusterId`` or ``ClusterId``
       environment variable, if any.
    3. The current user's key file. On Windows, each user runs their own Discovery Service and
       publishes its key file under ``%LOCALAPPDATA%``.
    4. The machine-wide key file under ``%ProgramData%``, which older Discovery Service versions
       publish and newer versions publish only in compatibility mode. A compatibility-mode key file
       may belong to another user's instance, so it is used only if this user's own instance does
       not start.

    If no Discovery Service is running, this starts one and waits for it to publish a key file.
    """
    address = _get_discovery_service_address_from_environment()
    if address is not None:
        _logger.debug(
            "Discovery service address from %s: %s", _DISCOVERY_SERVICE_ADDRESS_ENV_VAR, address
        )
        return address

    key_file_path = _ensure_discovery_service_started(_get_cluster_id())
    _logger.debug("Discovery service key file path: %s", key_file_path)
    return _read_discovery_service_address(key_file_path)


def _get_discovery_service_address_from_environment() -> str | None:
    address = os.environ.get(_DISCOVERY_SERVICE_ADDRESS_ENV_VAR, "").strip()
    if not address:
        return None
    host, separator, port = address.rpartition(":")
    if not separator or not host or not port.isdigit() or not 0 < int(port) <= 65535:
        raise ValueError(
            f"The {_DISCOVERY_SERVICE_ADDRESS_ENV_VAR} environment variable must be a host:port "
            f"address, not {address!r}."
        )
    return address


def _get_cluster_id() -> str | None:
    # To support operating systems other than Windows (and match Discovery Service behavior),
    # we would likely want to make this check case-insensitive.
    cluster_id = os.environ.get(
        _DISCOVERY_SERVICE_ENV_VAR_PREFIX + _DISCOVERY_SERVICE_CLUSTER_ID_ENV_VAR
    )
    if not cluster_id:
        cluster_id = os.environ.get(_DISCOVERY_SERVICE_CLUSTER_ID_ENV_VAR)
    # Like the Discovery Service, treat an empty cluster ID as the default instance.
    return cluster_id or None


def _read_discovery_service_address(key_file_path: pathlib.Path) -> str:
    with _open_key_file(str(key_file_path)) as key_file:
        key_json = json.load(key_file)
        return "localhost:" + str(key_json["InsecurePort"])


def _ensure_discovery_service_started(cluster_id: str | None = None) -> pathlib.Path:
    """Finds the key file of a running Discovery Service, starting the service if necessary."""
    key_file_path = _find_running_key_file(cluster_id)
    if key_file_path is not None:
        return key_file_path

    exe_file_path = _get_discovery_service_location()
    global _discovery_service_subprocess  # save Popen object to avoid ResourceWarning
    _discovery_service_subprocess = _launch_service(exe_file_path)
    return _wait_for_started_key_file(cluster_id)


def _find_running_key_file(cluster_id: str | None) -> pathlib.Path | None:
    key_file_path = _get_key_file_path(cluster_id)
    if _service_already_running(key_file_path):
        return key_file_path

    # A machine-wide key file written by a per-user Discovery Service belongs to whichever user's
    # instance claimed compatibility mode, which may be another user's. Prefer starting this
    # user's own instance, and use that key file only as a last resort.
    legacy_key_file_path = _get_legacy_key_file_path(cluster_id)
    if (
        legacy_key_file_path is not None
        and _service_already_running(legacy_key_file_path)
        and not _is_written_by_per_user_service(legacy_key_file_path)
    ):
        return legacy_key_file_path
    return None


def _wait_for_started_key_file(cluster_id: str | None) -> pathlib.Path:
    """Waits for a newly started Discovery Service to publish its key file."""
    return _wait_for_key_file(_get_key_file_path(cluster_id), _get_legacy_key_file_path(cluster_id))


def _wait_for_key_file(
    key_file_path: pathlib.Path, legacy_key_file_path: pathlib.Path | None
) -> pathlib.Path:
    timeout_time = time.time() + _START_SERVICE_TIMEOUT
    while True:
        if _can_open_key_file(key_file_path):
            return key_file_path
        # An older Discovery Service publishes only the machine-wide key file.
        if (
            legacy_key_file_path is not None
            and _can_open_key_file(legacy_key_file_path)
            and not _is_written_by_per_user_service(legacy_key_file_path)
        ):
            return legacy_key_file_path
        if time.time() >= timeout_time:
            break
        time.sleep(_START_SERVICE_POLLING_INTERVAL)

    if legacy_key_file_path is not None and _can_open_key_file(legacy_key_file_path):
        _logger.warning(
            "Timed out waiting for this user's discovery service to start. Using the "
            "compatibility-mode discovery service from %s, which may belong to another user.",
            legacy_key_file_path,
        )
        return legacy_key_file_path
    raise TimeoutError("Timed out waiting for discovery service to start")


def _can_open_key_file(key_file_path: pathlib.Path) -> bool:
    try:
        with _open_key_file(str(key_file_path)) as _:
            return True
    except OSError:
        return False


def _is_written_by_per_user_service(key_file_path: pathlib.Path) -> bool:
    try:
        with _open_key_file(str(key_file_path)) as key_file:
            key_json = json.load(key_file)
    except (OSError, ValueError):
        return False
    return isinstance(key_json, dict) and _KEY_FILE_PROCESS_ID_PROPERTY in key_json


def _get_discovery_service_location() -> pathlib.PurePath:
    """Gets the location of the discovery service process executable."""
    registration_json_path = _get_registration_json_file_path()
    registration_json_obj = json.loads(registration_json_path.read_text())
    return registration_json_path.parent / registration_json_obj["discovery"]["path"]


def _get_registration_json_file_path() -> pathlib.Path:
    if sys.platform == "win32":
        json_path = _get_nipath("NISHAREDDIR64") / "Services" / "NIServices.json"
        if not json_path.exists():
            json_path = (
                _get_nipath("NISHAREDDIR64") / "MeasurementLink" / "MeasurementLinkServices.json"
            )
        return json_path
    else:
        raise NotImplementedError("Platform not supported")


def _key_file_exists(key_file_path: pathlib.Path) -> bool:
    return key_file_path.is_file() and key_file_path.stat().st_size > 0


def _start_service(
    exe_file_path: pathlib.PurePath, key_file_path: pathlib.Path
) -> subprocess.Popen:
    """Starts the service at the specified path and wait for the service to get up and running."""
    discovery_service_subprocess = _launch_service(exe_file_path)
    _wait_for_key_file(key_file_path, _get_legacy_counterpart(key_file_path))
    return discovery_service_subprocess


def _get_legacy_counterpart(key_file_path: pathlib.Path) -> pathlib.Path | None:
    """Gets the machine-wide key file that an older Discovery Service publishes instead."""
    try:
        if key_file_path.parent != _get_key_file_directory():
            return None
        return _get_legacy_key_file_directory() / key_file_path.name
    except (NotImplementedError, OSError):
        return None


def _launch_service(exe_file_path: pathlib.PurePath) -> subprocess.Popen:
    """Starts the service at the specified path without waiting for it to publish a key file."""
    kwargs: dict[str, Any] = {}
    if sys.platform == "win32":
        # Terminating the measurement service should not terminate the discovery service.
        kwargs["creationflags"] = subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.DETACHED_PROCESS
    # The EXE file path comes from the registration JSON, which is installed in
    # a trusted location (e.g. NISHAREDDIR64).
    return subprocess.Popen(  # nosec: B603
        [exe_file_path],
        cwd=exe_file_path.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def _service_already_running(key_file_path: pathlib.Path) -> bool:
    try:
        _delete_existing_key_file(key_file_path)
    except OSError:
        return True
    return False


def _delete_existing_key_file(key_file_path: pathlib.Path) -> None:
    if _key_file_exists(key_file_path):
        with key_file_path.open("w") as _:
            pass
        key_file_path.unlink()


def _get_key_file_path(cluster_id: str | None = None) -> pathlib.Path:
    """Gets the path of the key file that the current user's Discovery Service publishes."""
    return _get_key_file_directory() / _get_key_file_name(cluster_id)


def _get_legacy_key_file_path(cluster_id: str | None = None) -> pathlib.Path | None:
    """Gets the path of the machine-wide key file, or None if there isn't one."""
    try:
        return _get_legacy_key_file_directory() / _get_key_file_name(cluster_id)
    except (NotImplementedError, OSError):
        # The machine-wide key file exists only on Windows, and NIPUBAPPDATADIR may be missing,
        # for example when no NI installer has run.
        return None


def _get_key_file_name(cluster_id: str | None) -> str:
    if cluster_id:
        return f"DiscoveryService_{cluster_id}.json"
    return "DiscoveryService.json"


def _get_key_file_directory() -> pathlib.Path:
    """Gets the current user's key file directory.

    On Windows, each user runs their own Discovery Service, which publishes its key files under
    %LOCALAPPDATA% rather than the machine-wide %ProgramData% directory that every user can write.
    """
    if sys.platform == "win32":
        local_app_data = pathlib.Path(shell.SHGetKnownFolderPath(shellcon.FOLDERID_LocalAppData))
        return (
            local_app_data
            / "National Instruments"
            / "MeasurementLink"
            / "Discovery"
            / _get_version()
        )
    else:
        raise NotImplementedError("Platform not supported")


def _get_legacy_key_file_directory() -> pathlib.Path:
    """Gets the machine-wide key file directory used by older Discovery Service versions."""
    if sys.platform == "win32":
        return _get_nipath("NIPUBAPPDATADIR") / "MeasurementLink" / "Discovery" / _get_version()
    else:
        raise NotImplementedError("Platform not supported")


def _get_version() -> str:
    return discovery_service_pb2.DESCRIPTOR.package.split(".")[-1]


def _open_key_file(path: str) -> typing.TextIO:
    if sys.platform == "win32":
        # Use the Win32 API to specify the share mode. Otherwise, opening the file throws
        # PermissionError due to a sharing violation. This is a workaround for
        # https://github.com/python/cpython/issues/59449
        # (Support for opening files with FILE_SHARE_DELETE on Windows).
        try:
            win32_file_handle = win32file.CreateFile(
                path,
                win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ
                | win32file.FILE_SHARE_WRITE
                | win32file.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                0,
                None,
            )
        except win32file.error as e:
            raise OSError(None, e.strerror, path, e.winerror) from e

        # The CRT file descriptor takes ownership of the Win32 file handle.
        # os.O_TEXT is unnecessary because Python handles newline conversion.
        crt_file_descriptor = msvcrt.open_osfhandle(win32_file_handle.handle, os.O_RDONLY)
        win32_file_handle.Detach()

        # The Python file object takes ownership of the CRT file descriptor. Closing the Python
        # file object closes the underlying Win32 file handle.
        return os.fdopen(crt_file_descriptor, "r", encoding="utf-8-sig")
    else:
        return open(path)


def _get_nipath(name: str) -> pathlib.Path:
    if sys.platform == "win32":
        access: int = winreg.KEY_READ
        if "64" in name:
            access |= winreg.KEY_WOW64_64KEY
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\National Instruments\Common\Installer",
            access=access,
        ) as key:
            value, type = winreg.QueryValueEx(key, name)
            assert type == winreg.REG_SZ
            return pathlib.Path(value)
    else:
        raise NotImplementedError("Platform not supported")

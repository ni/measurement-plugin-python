"""Support functions for the MeasurementLink discovery service."""

import json
import logging
import os
import pathlib
import subprocess
import sys
import time
import typing
from typing import Any, Dict, Optional

from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
)

if sys.platform == "win32":
    import msvcrt
    import winreg

    import win32con
    import win32file

_logger = logging.getLogger(__name__)
# Save Popen object to avoid "ResourceWarning: subprocess N is still running"
_discovery_service_subprocess: Optional[subprocess.Popen] = None

_START_SERVICE_TIMEOUT = 30.0
_START_SERVICE_POLLING_INTERVAL = 100e-3


def _get_discovery_service_address() -> str:
    key_file_path = _get_key_file_path()
    _ensure_discovery_service_started(key_file_path)
    _logger.debug("Discovery service key file path: %s", key_file_path)
    with _open_key_file(str(key_file_path)) as key_file:
        key_json = json.load(key_file)
        return "localhost:" + key_json["InsecurePort"]


def _ensure_discovery_service_started(key_file_path: pathlib.Path) -> None:
    """Check whether discovery service already running, if not start the discovery service."""
    if _service_already_running(key_file_path):
        return

    exe_file_path = _get_discovery_service_location()
    global _discovery_service_subprocess  # save Popen object to avoid ResourceWarning
    _discovery_service_subprocess = _start_service(exe_file_path, key_file_path)


def _get_discovery_service_location() -> pathlib.PurePath:
    """Gets the location of the discovery service process executable."""
    registration_json_path = _get_registration_json_file_path()
    registration_json_obj = json.loads(registration_json_path.read_text())
    return registration_json_path.parent / registration_json_obj["discovery"]["path"]


def _get_registration_json_file_path() -> pathlib.Path:
    if sys.platform == "win32":
        return _get_nipath("NISHAREDDIR64") / "MeasurementLink" / "MeasurementLinkServices.json"
    else:
        raise NotImplementedError("Platform not supported")


def _key_file_exists(key_file_path: pathlib.Path) -> bool:
    return key_file_path.is_file() and key_file_path.stat().st_size > 0


def _start_service(
    exe_file_path: pathlib.PurePath, key_file_path: pathlib.Path
) -> subprocess.Popen:
    """Starts the service at the specified path and wait for the service to get up and running."""
    kwargs: Dict[str, Any] = {}
    if sys.platform == "win32":
        # Terminating the measurement service should not terminate the discovery service.
        kwargs["creationflags"] = subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.DETACHED_PROCESS
    discovery_service_subprocess = subprocess.Popen(
        [exe_file_path],
        cwd=exe_file_path.parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    # After the execution of process, check for key file existence in the path
    # stop checking after 30 seconds have elapsed and throw error
    timeout_time = time.time() + _START_SERVICE_TIMEOUT
    while True:
        try:
            with _open_key_file(str(key_file_path)) as _:
                return discovery_service_subprocess
        except OSError:
            pass
        if time.time() >= timeout_time:
            raise TimeoutError("Timed out waiting for discovery service to start")
        time.sleep(_START_SERVICE_POLLING_INTERVAL)


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


def _get_key_file_path(cluster_id: Optional[str] = None) -> pathlib.Path:
    if cluster_id is not None:
        return _get_key_file_directory() / f"DiscoveryService_{cluster_id}.json"
    return _get_key_file_directory() / "DiscoveryService.json"


def _get_key_file_directory() -> pathlib.Path:
    version = discovery_service_pb2.DESCRIPTOR.package.split(".")[-1]
    if sys.platform == "win32":
        return _get_nipath("NIPUBAPPDATADIR") / "MeasurementLink" / "Discovery" / version
    else:
        raise NotImplementedError("Platform not supported")


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
        return open(path, "r")


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

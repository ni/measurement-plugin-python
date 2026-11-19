"""Tests for resolving the Discovery Service address."""

from __future__ import annotations

import json
import os
import pathlib
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurement_plugin_sdk_service.discovery._support import (
    _get_discovery_service_address,
    _get_key_file_directory,
    _get_key_file_path,
    _get_legacy_key_file_directory,
    _start_service,
)

if sys.platform == "win32":
    import win32con
    import win32file

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Discovery Service key files are only supported on Windows."
)

_SUPPORT_MODULE = "ni_measurement_plugin_sdk_service.discovery._support"
_UTF8_BOM = b"\xef\xbb\xbf"
_REGISTRATION_FILE_CONTENT = {"discovery": {"path": "Discovery/NI.Discovery.V1.Service.exe"}}


class _KeyFilePublisher:
    """Publishes key files the way the Discovery Service does.

    The Discovery Service writes key files with a UTF-8 byte order mark and keeps them open without
    write sharing, which is how clients tell a running instance from a stale key file.
    """

    def __init__(self) -> None:
        self._handles: list[Any] = []

    def publish(
        self,
        path: pathlib.Path,
        insecure_port: str,
        *,
        per_user_service: bool = True,
        bom: bool = True,
    ) -> None:
        content: dict[str, Any] = {
            "InsecurePort": insecure_port,
            "SecurePort": "",
            "Http1ProxyPort": "1",
        }
        if per_user_service:
            content.update({"ProcessId": 1234, "StartTime": "2026-11-17T18:00:00.0000000Z"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((_UTF8_BOM if bom else b"") + json.dumps(content).encode())
        if sys.platform == "win32":
            self._handles.append(
                win32file.CreateFile(
                    str(path),
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None,
                )
            )
        else:
            pytest.skip("Windows-only test")

    def close(self) -> None:
        for handle in self._handles:
            handle.Close()
        self._handles.clear()


@pytest.fixture
def key_files() -> Generator[_KeyFilePublisher, None, None]:
    publisher = _KeyFilePublisher()
    yield publisher
    publisher.close()


@pytest.fixture
def per_user_directory(tmp_path: pathlib.Path, mocker: MockerFixture) -> pathlib.Path:
    directory = tmp_path / "LocalAppData" / "Discovery" / "v1"
    mocker.patch(f"{_SUPPORT_MODULE}._get_key_file_directory", return_value=directory)
    return directory


@pytest.fixture
def legacy_directory(tmp_path: pathlib.Path, mocker: MockerFixture) -> pathlib.Path:
    directory = tmp_path / "ProgramData" / "Discovery" / "v1"
    mocker.patch(f"{_SUPPORT_MODULE}._get_legacy_key_file_directory", return_value=directory)
    return directory


@pytest.fixture(autouse=True)
def discovery_environment(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for name in ("DISCOVERY_SERVICE_ADDRESS", "NIDiscovery_ClusterId", "ClusterId"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def mock_popen(mocker: MockerFixture, tmp_path: pathlib.Path) -> Mock:
    registration_json_path = tmp_path / "NIServices.json"
    registration_json_path.write_text(json.dumps(_REGISTRATION_FILE_CONTENT))
    mocker.patch(
        f"{_SUPPORT_MODULE}._get_registration_json_file_path",
        return_value=registration_json_path,
    )
    return mocker.patch("subprocess.Popen")


def test___address_environment_variable_set___get_discovery_service_address___returns_environment_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    discovery_environment: pytest.MonkeyPatch,
    mock_popen: Mock,
) -> None:
    discovery_environment.setenv("DISCOVERY_SERVICE_ADDRESS", "localhost:50000")
    discovery_environment.setenv("NIDiscovery_ClusterId", "cluster")
    key_files.publish(per_user_directory / "DiscoveryService_cluster.json", "50001")
    key_files.publish(per_user_directory / "DiscoveryService.json", "50002")
    key_files.publish(legacy_directory / "DiscoveryService.json", "42000", per_user_service=False)

    address = _get_discovery_service_address()

    assert address == "localhost:50000"
    mock_popen.assert_not_called()


@pytest.mark.parametrize("address", ["localhost", "localhost:", ":42000", "localhost:port"])
def test___invalid_address_environment_variable___get_discovery_service_address___raises_value_error(
    discovery_environment: pytest.MonkeyPatch, address: str
) -> None:
    discovery_environment.setenv("DISCOVERY_SERVICE_ADDRESS", address)

    with pytest.raises(ValueError, match="DISCOVERY_SERVICE_ADDRESS"):
        _get_discovery_service_address()


@pytest.mark.parametrize("cluster_id_env_var", ["NIDiscovery_ClusterId", "ClusterId"])
def test___cluster_selected___get_discovery_service_address___returns_cluster_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    discovery_environment: pytest.MonkeyPatch,
    mock_popen: Mock,
    cluster_id_env_var: str,
) -> None:
    discovery_environment.setenv(cluster_id_env_var, "cluster")
    key_files.publish(per_user_directory / "DiscoveryService_cluster.json", "50001")
    key_files.publish(per_user_directory / "DiscoveryService.json", "50002")
    key_files.publish(legacy_directory / "DiscoveryService.json", "42000", per_user_service=False)

    address = _get_discovery_service_address()

    assert address == "localhost:50001"
    mock_popen.assert_not_called()


def test___cluster_selected_with_older_discovery_service___get_discovery_service_address___returns_legacy_cluster_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    discovery_environment: pytest.MonkeyPatch,
    mock_popen: Mock,
) -> None:
    discovery_environment.setenv("NIDiscovery_ClusterId", "cluster")
    key_files.publish(per_user_directory / "DiscoveryService.json", "50002")
    key_files.publish(
        legacy_directory / "DiscoveryService_cluster.json", "50003", per_user_service=False
    )

    address = _get_discovery_service_address()

    assert address == "localhost:50003"
    mock_popen.assert_not_called()


def test___empty_cluster_id___get_discovery_service_address___returns_per_user_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    discovery_environment: pytest.MonkeyPatch,
    mock_popen: Mock,
) -> None:
    discovery_environment.setenv("ClusterId", "")
    key_files.publish(per_user_directory / "DiscoveryService.json", "50002")

    address = _get_discovery_service_address()

    assert address == "localhost:50002"
    mock_popen.assert_not_called()


def test___per_user_and_legacy_key_files___get_discovery_service_address___returns_per_user_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
) -> None:
    key_files.publish(per_user_directory / "DiscoveryService.json", "50002")
    key_files.publish(legacy_directory / "DiscoveryService.json", "42000")

    address = _get_discovery_service_address()

    assert address == "localhost:50002"
    mock_popen.assert_not_called()


@pytest.mark.parametrize("bom", [True, False])
def test___older_discovery_service_running___get_discovery_service_address___returns_legacy_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
    bom: bool,
) -> None:
    key_files.publish(
        legacy_directory / "DiscoveryService.json", "42000", per_user_service=False, bom=bom
    )

    address = _get_discovery_service_address()

    assert address == "localhost:42000"
    mock_popen.assert_not_called()


def test___key_file_with_bom_and_extra_fields___get_discovery_service_address___returns_insecure_port(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    mocker: MockerFixture,
) -> None:
    per_user_directory.mkdir(parents=True)
    key_file_path = per_user_directory / "DiscoveryService.json"
    key_file_path.write_bytes(
        _UTF8_BOM
        + b'{"InsecurePort":"50002","SecurePort":"50004","Http1ProxyPort":"50005",'
        + b'"ProcessId":1234,"StartTime":"2026-11-17T18:00:00.0000000Z","Unknown":{"a":[1]}}'
    )
    mocker.patch(f"{_SUPPORT_MODULE}._service_already_running", return_value=True)

    address = _get_discovery_service_address()

    assert address == "localhost:50002"


def test___only_another_users_compatibility_key_file___get_discovery_service_address___starts_and_returns_per_user_service(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
) -> None:
    key_files.publish(legacy_directory / "DiscoveryService.json", "42000")
    mock_popen.side_effect = lambda *args, **kwargs: key_files.publish(
        per_user_directory / "DiscoveryService.json", "50002"
    )

    address = _get_discovery_service_address()

    assert address == "localhost:50002"
    mock_popen.assert_called_once()


def test___no_key_files_and_older_discovery_service_installed___get_discovery_service_address___starts_and_returns_legacy_service(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
) -> None:
    mock_popen.side_effect = lambda *args, **kwargs: key_files.publish(
        legacy_directory / "DiscoveryService.json", "42000", per_user_service=False
    )

    address = _get_discovery_service_address()

    assert address == "localhost:42000"
    mock_popen.assert_called_once()


def test___per_user_service_never_starts_with_compatibility_key_file___get_discovery_service_address___returns_compatibility_address(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocker.patch(f"{_SUPPORT_MODULE}._START_SERVICE_TIMEOUT", 0.3)
    key_files.publish(legacy_directory / "DiscoveryService.json", "42000")

    address = _get_discovery_service_address()

    assert address == "localhost:42000"
    mock_popen.assert_called_once()
    assert "compatibility-mode discovery service" in caplog.text


def test___stale_key_files___get_discovery_service_address___deletes_them_and_starts_service(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
) -> None:
    per_user_directory.mkdir(parents=True)
    legacy_directory.mkdir(parents=True)
    stale_per_user_key_file = per_user_directory / "DiscoveryService.json"
    stale_legacy_key_file = legacy_directory / "DiscoveryService.json"
    stale_per_user_key_file.write_text('{"InsecurePort": "1"}')
    stale_legacy_key_file.write_text('{"InsecurePort": "2"}')

    def start_service(*args: Any, **kwargs: Any) -> None:
        # Publishing fails if the client left the stale key file in place.
        assert not stale_per_user_key_file.exists()
        assert not stale_legacy_key_file.exists()
        key_files.publish(stale_per_user_key_file, "50002")

    mock_popen.side_effect = start_service

    address = _get_discovery_service_address()

    assert address == "localhost:50002"
    mock_popen.assert_called_once()


def test___legacy_directory_unavailable___get_discovery_service_address___starts_and_returns_per_user_service(
    per_user_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(f"{_SUPPORT_MODULE}._get_nipath", side_effect=FileNotFoundError)
    mock_popen.side_effect = lambda *args, **kwargs: key_files.publish(
        per_user_directory / "DiscoveryService.json", "50002"
    )

    address = _get_discovery_service_address()

    assert address == "localhost:50002"


def test___older_discovery_service___start_service_with_per_user_key_file_path___waits_for_legacy_key_file(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    key_files: _KeyFilePublisher,
    mock_popen: Mock,
    tmp_path: pathlib.Path,
) -> None:
    # Test utilities in dependent packages pair _get_key_file_path() with _start_service().
    mock_popen.side_effect = lambda *args, **kwargs: key_files.publish(
        legacy_directory / "DiscoveryService.json", "42000", per_user_service=False
    )

    _start_service(tmp_path / "Discovery" / "NI.Discovery.V1.Service.exe", _get_key_file_path())

    mock_popen.assert_called_once()


def test___windows___get_key_file_directories___returns_per_user_and_machine_wide_directories(
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        f"{_SUPPORT_MODULE}._get_nipath",
        return_value=pathlib.Path(r"C:\ProgramData\National Instruments"),
    )

    per_user_directory = _get_key_file_directory()
    legacy_directory = _get_legacy_key_file_directory()

    assert per_user_directory == pathlib.Path(
        os.environ["LOCALAPPDATA"], "National Instruments", "MeasurementLink", "Discovery", "v1"
    )
    assert legacy_directory == pathlib.Path(
        r"C:\ProgramData\National Instruments\MeasurementLink\Discovery\v1"
    )


def test___no_discovery_service_starts___get_discovery_service_address___raises_timeout_error(
    per_user_directory: pathlib.Path,
    legacy_directory: pathlib.Path,
    mock_popen: Mock,
    mocker: MockerFixture,
) -> None:
    mocker.patch(f"{_SUPPORT_MODULE}._START_SERVICE_TIMEOUT", 0.3)

    with pytest.raises(TimeoutError):
        _get_discovery_service_address()

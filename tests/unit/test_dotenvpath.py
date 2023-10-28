from pathlib import Path

import pytest

import ni_measurementlink_service
from ni_measurementlink_service import _dotenvpath


@pytest.mark.parametrize("exists", [False, True])
def test___exists_varies___has_dotenv_file___returns_exists(
    dotenv_exists: bool, tmp_path: Path
) -> None:
    if dotenv_exists:
        (tmp_path / ".env").write_text("")
    subdirs = [tmp_path / "a", tmp_path / "a" / "b", tmp_path / "a" / "b" / "c"]
    for dir in subdirs:
        dir.mkdir()

    assert _dotenvpath._has_dotenv_file(tmp_path) == dotenv_exists
    assert all([_dotenvpath._has_dotenv_file(p) == dotenv_exists for p in subdirs])


def test___get_caller_path___returns_this_modules_path() -> None:
    assert _dotenvpath._get_caller_path() == Path(__file__)


def test___get_nims_path___returns_nims_path() -> None:
    assert _dotenvpath._get_nims_path() == Path(ni_measurementlink_service.__file__)


def test___get_script_or_exe_path___returns_pytest_path() -> None:
    path = _dotenvpath._get_script_or_exe_path()

    assert path.parent.name in ["pytest", "pytest.exe"] and path.name == "__main__.py"

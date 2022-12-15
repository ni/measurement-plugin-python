#!/usr/bin/env python3
"""Install all example services."""

import os
import pathlib
import shutil
import subprocess

EXAMPLES_PATH = pathlib.Path(__file__).parent.parent / "examples"
SERVICES_PATH = (
    pathlib.Path(os.environ["ProgramData"])
    / "National Instruments"
    / "MeasurementLink"
    / "Services"
)


def main():
    """Install all example services."""
    _deactivate_venv()
    for example_path in EXAMPLES_PATH.iterdir():
        if not (example_path / "pyproject.toml").exists():
            continue

        print(f"{example_path.name}:")

        poetry_lock = example_path / "poetry.lock"
        if poetry_lock.exists():
            print(f"Deleting lock file {poetry_lock}")
            poetry_lock.unlink()

        venv_dir = example_path / ".venv"
        if venv_dir.is_dir():
            print(f"Deleting virtualenv {venv_dir}")
            shutil.rmtree(venv_dir)

        print(f"Installing dependencies")
        subprocess.run(["poetry", "-v", "install"], check=True, cwd=example_path)

        install_path = SERVICES_PATH / example_path.name
        if install_path.is_dir():
            print(f"Deleting example from {install_path}")
            shutil.rmtree(install_path)

        print(f"Installing example into {install_path}")
        shutil.copytree(example_path, install_path)

        print("")


def _deactivate_venv():
    """Deactivate the current venv.

    This is a workaround for https://github.com/python-poetry/poetry/issues/4055
    Option to force Poetry to create a virtual environment, even if a virtual env is active

    """
    if "VIRTUAL_ENV" in os.environ:
        for var in os.environ.keys():
            if var.startswith("_OLD_VIRTUAL_"):
                original_var = var.replace("_OLD_VIRTUAL_", "")
                os.environ[original_var] = os.environ[var]
                del os.environ[var]
        del os.environ["VIRTUAL_ENV"]


if __name__ == "__main__":
    main()

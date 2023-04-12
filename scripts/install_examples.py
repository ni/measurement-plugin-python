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
    clean_env = _get_clean_env()
    for example_path in EXAMPLES_PATH.iterdir():
        if not (example_path / "pyproject.toml").exists():
            continue

        print(f"{example_path.name}:")

        install_path = SERVICES_PATH / example_path.name
        if install_path.is_dir():
            print(f"Deleting example from {install_path}")
            shutil.rmtree(install_path)

        print(f"Installing example into {install_path}")
        shutil.copytree(example_path, install_path, ignore=shutil.ignore_patterns(".venv"))

        poetry_lock = install_path / "poetry.lock"
        if poetry_lock.exists():
            print(f"Deleting lock file {poetry_lock}")
            poetry_lock.unlink()

        venv_dir = install_path / ".venv"
        if venv_dir.is_dir():
            print(f"Deleting virtualenv {venv_dir}")
            shutil.rmtree(venv_dir)

        print(f"Installing dependencies")
        subprocess.run(["poetry", "-v", "install"], check=True, cwd=install_path, env=clean_env)

        print("")


def _get_clean_env():
    """Get a clean environment with no venv activated.

    This is a workaround for https://github.com/python-poetry/poetry/issues/4055
    Option to force Poetry to create a virtual environment, even if a virtual env is active

    """
    env = os.environ.copy()
    if env.pop("VIRTUAL_ENV", None) is not None:
        for var in os.environ.keys():
            value = env.pop(f"_OLD_VIRTUAL_{var}", None)
            if value is not None:
                env[var] = value
    return env


if __name__ == "__main__":
    main()

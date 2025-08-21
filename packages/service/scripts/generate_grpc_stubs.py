#!/usr/bin/env python3
"""Generates gRPC Python stubs from proto files."""

import pathlib
import shutil
from collections.abc import Sequence

import grpc_tools.protoc
import pkg_resources

PROTO_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "third_party" / "ni-apis"
TEST_STUBS_PATH = pathlib.Path(__file__).parent.parent / "tests" / "utilities" / "stubs"
TEST_PROTO_PATH = TEST_STUBS_PATH
TEST_PROTO_FILES = list(TEST_PROTO_PATH.rglob("*.proto"))


def main():
    """Generate test gRPC Python stubs."""
    generate_python_files(TEST_STUBS_PATH, TEST_PROTO_PATH, TEST_PROTO_FILES, PROTO_PATH)


def is_relative_to(path: pathlib.PurePath, other: pathlib.PurePath) -> bool:
    """Return whether or not this path is relative to the other path."""
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def generate_python_files(
    stubs_path: pathlib.Path,
    proto_path: pathlib.Path,
    proto_files: Sequence[pathlib.Path],
    alternate_proto_path: pathlib.Path = "",
):
    """Generate python files from .proto files with protoc."""
    arguments = [
        "protoc",
        f"--proto_path={str(proto_path)}",
        f"--proto_path={pkg_resources.resource_filename('grpc_tools', '_proto')}",
        f"--python_out={str(stubs_path)}",
        f"--mypy_out={str(stubs_path)}",
        f"--grpc_python_out={str(stubs_path)}",
        f"--mypy_grpc_out={str(stubs_path)}",
    ]
    if alternate_proto_path != "":
        arguments += (f"--proto_path={str(alternate_proto_path)}",)

    arguments += [str(path.relative_to(proto_path)).replace("\\", "/") for path in proto_files]

    grpc_tools.protoc.main(arguments)


if __name__ == "__main__":
    main()

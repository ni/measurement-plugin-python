#!/usr/bin/env python3
"""Generates gRPC Python stubs from proto files."""

import pathlib
from collections.abc import Sequence

import grpc_tools.protoc
import pkg_resources

STUBS_NAMESPACE = "tests.utilities.measurements.non_streaming_data_measurement._stubs"
PROTO_PARENT_NAMESPACES = ["ni.measurementlink", "nidevice_grpc", "ni.protobuf.types"]
STUBS_PATH = pathlib.Path(__file__).parent.parent / STUBS_NAMESPACE.replace(".", "/")
STUBS_PROTO_PATH = STUBS_PATH
STUBS_PROTO_FILES = list(STUBS_PROTO_PATH.rglob("*.proto"))


def main():
    """Generate and fixup gRPC Python stubs."""
    generate_python_files(STUBS_PATH, STUBS_PROTO_PATH, STUBS_PROTO_FILES)
    fix_import_paths(STUBS_PROTO_PATH, STUBS_PATH, STUBS_NAMESPACE, PROTO_PARENT_NAMESPACES)


def generate_python_files(
    stubs_path: pathlib.Path,
    proto_path: pathlib.Path,
    proto_files: Sequence[pathlib.Path],
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

    arguments += [str(path.relative_to(proto_path)).replace("\\", "/") for path in proto_files]

    grpc_tools.protoc.main(arguments)


def fix_import_paths(
    protos_path: pathlib.Path,
    stubs_path: pathlib.Path,
    stubs_namespace: str,
    proto_parent_namespaces: Sequence[str],
):
    """Fix import paths of generated files."""
    print("Fixing import paths")
    grpc_codegened_file_paths = list(protos_path.rglob("*pb2*py"))
    stubs_codegened_file_paths = list(stubs_path.rglob("*pb2*py"))
    imports_to_fix = [path.stem for path in stubs_codegened_file_paths if path.parent == stubs_path]
    imports_to_alias = [
        ".".join(path.relative_to(stubs_path).with_suffix("").parts)
        for path in stubs_codegened_file_paths
        if path.stem not in imports_to_fix
    ]
    grpc_codegened_file_paths.extend(protos_path.rglob("*pb2*pyi"))
    for path in grpc_codegened_file_paths:
        print(f"Processing {path}")
        data = path.read_bytes()
        for name in imports_to_fix:
            data = data.replace(
                f"import {name}".encode(), f"from {stubs_namespace} import {name}".encode()
            )
        for namespace in proto_parent_namespaces:
            data = data.replace(
                f"from {namespace}".encode(),
                f"from {stubs_namespace}.{namespace}".encode(),
            )
        if path.suffix == ".pyi":
            for name in imports_to_alias:
                alias = name.replace(".", "_")
                data = data.replace(
                    f"import {name}\n".encode(),
                    f"import {stubs_namespace}.{name} as {alias}\n".encode(),
                )
                data = data.replace(
                    f"{name}.".encode(),
                    f"{alias}.".encode(),
                )
        path.write_bytes(data)


if __name__ == "__main__":
    main()

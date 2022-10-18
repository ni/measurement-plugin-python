"""Generates gRPC Python stubs from proto files."""

import pathlib

import black
import grpc_tools.protoc
import pkg_resources
from black.mode import Mode


STUBS_NAMESPACE = "ni_measurement_service._internal.stubs"
STUBS_PATH = pathlib.Path(__file__).parent.parent / STUBS_NAMESPACE.replace(".", "/")
PROTO_PATH = STUBS_PATH / "proto"
PROTO_FILES = list(PROTO_PATH.rglob("*.proto"))


def main():
    """Generate and fixup gRPC Python stubs."""
    generate_python_files()
    fix_import_paths()
    blacken_code()


def generate_python_files():
    """Generate python files from .proto files with protoc."""
    arguments = [
        "protoc",
        f"--proto_path={str(PROTO_PATH)}",
        f"--proto_path={pkg_resources.resource_filename('grpc_tools', '_proto')}",
        f"--python_out={str(STUBS_PATH)}",
        f"--grpc_python_out={str(STUBS_PATH)}",
    ]
    arguments += [str(path.relative_to(PROTO_PATH)).replace("\\", "/") for path in PROTO_FILES]

    grpc_tools.protoc.main(arguments)


def fix_import_paths():
    """Fix import paths of generated files."""
    print("Fixing import paths")
    grpc_codegened_file_paths = list(STUBS_PATH.glob("*pb2*py"))
    imports_to_fix = [path.stem for path in grpc_codegened_file_paths]
    for path in grpc_codegened_file_paths:
        print(f"Processing {path}")
        data = path.read_bytes()
        for name in imports_to_fix:
            data = data.replace(
                f"import {name}".encode(), f"from {STUBS_NAMESPACE} import {name}".encode()
            )

        data = data.replace(
            "from ni.measurements".encode(), f"from {STUBS_NAMESPACE}.ni.measurements".encode()
        )
        path.write_bytes(data)


def blacken_code():
    """Run black on generated files."""
    print("Running black")
    for py_path in STUBS_PATH.rglob("*.py"):
        if black.format_file_in_place(
            src=py_path, fast=False, mode=Mode(line_length=100), write_back=black.WriteBack.YES
        ):
            print(f"reformatted {py_path}")


if __name__ == "__main__":
    main()

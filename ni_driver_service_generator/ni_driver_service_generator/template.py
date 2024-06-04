
import ast
import os
import pathlib
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

import click
from mako.template import Template
import grpc_tools.protoc
import pkg_resources


class ClassVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes : Dict[str, List[Dict[str, Union[str, List[str]]]]] = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self.get_method_info(item)
                methods.append(method_info)
        self.classes[class_name] = methods
        self.generic_visit(node)  # Continue visiting other nodes

    def get_method_info(self, node):
        method_name = node.name
        params = self.get_parameters(node)
        return_type = self.get_annotation(node.returns)
        return {'name': method_name, 'params': params, 'return_type': return_type}

    def get_parameters(self, node):
        params = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = self.get_annotation(arg.annotation)
            params.append(f'{arg_name}: {arg_type}')
        # Handle varargs (*args)
        if node.args.vararg:
            vararg_type = self.get_annotation(node.args.vararg.annotation)
            params.append(f'*{node.args.vararg.arg}: {vararg_type}')
        # Handle keyword-only args
        for arg in node.args.kwonlyargs:
            arg_name = arg.arg
            arg_type = self.get_annotation(arg.annotation)
            params.append(f'{arg_name}: {arg_type}')
        # Handle kwargs (**kwargs)
        if node.args.kwarg:
            kwarg_type = self.get_annotation(node.args.kwarg.annotation)
            params.append(f'**{node.args.kwarg.arg}: {kwarg_type}')
        return params

    def get_annotation(self, annotation):
        if annotation is None:
            return 'None'
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return self.get_attribute_type(annotation)
        if isinstance(annotation, ast.Subscript):
            value = self.get_annotation(annotation.value)
            slice_ = self.get_annotation(annotation.slice)
            return f'{value}[{slice_}]'
        if isinstance(annotation, ast.Tuple):
            return ', '.join(self.get_annotation(elt) for elt in annotation.elts)
        if isinstance(annotation, ast.Index):  # For Python 3.8 and earlier
            return self.get_annotation(annotation.value)
        if isinstance(annotation, ast.Constant):  # For Python 3.9 and later
            return annotation.value
        return 'Any'

    def get_attribute_type(self, node):
        if isinstance(node.value, ast.Name):
            return f'{node.value.id}.{node.attr}'
        if isinstance(node.value, ast.Attribute):
            return f'{self.get_attribute_type(node.value)}.{node.attr}'
        return 'Any'


class MethodDef:
    name: str
    request_type: str
    return_type: str


def _validate_file_path(ctx: click.Context, param: click.Parameter, path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"The file path is invalid: {path}")

    return path

def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)

    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    try:
        return template.render(**template_args)
    except Exception as e:
        raise Exception(
            f'An error occurred while rendering template "{template_name}".'
        ) from e


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("wb") as fout:
        fout.write(output)


def fix_import_paths(
    protos_path: pathlib.Path,
    stubs_path: pathlib.Path,
    stubs_namespace: str,
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


def generate_python_files(
    stubs_path: Path,
    proto_path: Path,
    proto_files: Sequence[Path],
    alternate_proto_path: Path = "",
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


def get_global_functions(file_path):
    """
    Parse the Python file and return a list of global function names.
    """
    with open(file_path) as file:
        tree = ast.parse(file.read(), filename=file_path)

    global_functions = []
    
    # Traverse the AST and collect names of global functions
    for node in ast.iter_child_nodes(tree):
        # Check if the node is a function definition at the module level
        if isinstance(node, ast.FunctionDef):
            global_functions.append(node.name)
    
    return global_functions

@click.command()
@click.option(
    "-p",
    "--proto-path",
    callback=_validate_file_path,
    help="The path of the proto file.",
)
@click.option(
    "-s",
    "--stubs-dir",
    help="The directory for the generated files and stubs.",
)
def create_template(proto_path: str, stubs_dir: str):

    proto_file_path = Path(proto_path)
    file_name = proto_file_path.stem
    stubs_dir : Path = Path(stubs_dir) / "stubs"
    stubs_dir.mkdir(exist_ok=True, parents=True)
    generate_python_files(stubs_path=stubs_dir, proto_path=proto_file_path.parent, proto_files=[proto_file_path])
    fix_import_paths(protos_path=stubs_dir, stubs_path=stubs_dir, stubs_namespace="stubs")

    file_path = stubs_dir / f"{file_name}_pb2_grpc.pyi"

    with open(file_path) as stub_file:

        content = stub_file.read()
        program = ast.parse(content)

        visitor = ClassVisitor()
        visitor.visit(program)

        class_defs : Dict[str, List[MethodDef]] = {}
        for k,v in visitor.classes.items():
            if k.endswith("Servicer"):
                grpc_class_name = k
                class_name = grpc_class_name[:-1]
                methods: List[MethodDef] = []
                for value in v:
                    method_def = MethodDef()
                    method_def.name = value["name"]
                    method_def.request_type = ", ".join(value["params"]).replace("_ServicerContext", "grpc.ServicerContext").replace(": None", "")
                    method_def.return_type = value["return_type"]
                    methods.append(method_def)
                class_defs[k] = methods

    directory_out_path = stubs_dir.parent
    directory_out_path.mkdir(exist_ok=True, parents=True)
    function = get_global_functions(file_path)

    _create_file(
        "service.py.mako",
        f"{class_name}.py",
        directory_out_path,
        import_name=f"{file_name}",
        class_defs=class_defs,
    )
    _create_file(
        "main.py.mako",
        "main.py",
        directory_out_path,
        import_name=f"stubs.{file_name}",
        gen_file_name=class_name,
        class_name=class_name,
        method_name=function[0]
    )

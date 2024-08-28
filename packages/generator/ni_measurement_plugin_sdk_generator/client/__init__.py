"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
import sys
from typing import Any, List, Optional

import black
import click
from mako.template import Template
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool

from ni_measurement_plugin_sdk_generator.client._support import (
    camel_to_snake_case,
    get_configuration_metadata_by_index,
    get_configuration_parameters_with_type_and_default_values,
    get_measurement_service_stub,
    get_output_metadata_by_index,
    get_output_parameters_with_type,
    to_ordered_set,
)


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)
    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    return template.render(**template_args)


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args).decode("utf-8")
    formatted_output = black.format_str(
        src_contents=output,
        mode=black.Mode(line_length=100),
    )

    with output_file.open("w") as file:
        file.write(formatted_output)


def _remove_suffix(string: str) -> str:
    suffixes = ["_Python", "_LabVIEW"]
    for suffix in suffixes:
        if string.endswith(suffix):
            if sys.version_info >= (3, 9):
                return string.removesuffix(suffix)
            else:
                return string[0 : len(string) - len(suffix)]
    return string


@click.command()
@click.argument("measurement_service_class")
@click.option(
    "-m",
    "--module-name",
    help="Name for the Python Measurement Plug-In Client module.",
)
@click.option(
    "-c",
    "--class-name",
    help="Name for the Python Measurement Plug-In Client Class in the generated module.",
)
@click.option(
    "-o",
    "--directory-out",
    help="Output directory for Measurement Plug-In Client files. Default: '<current_directory>/<module_name>'",
)
def create_client(
    measurement_service_class: str,
    module_name: Optional[str],
    class_name: Optional[str],
    directory_out: Optional[str],
) -> None:
    """Generates a Python Measurement Plug-In Client module for the measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MEASUREMENT_SERVICE_CLASS: The service class of the measurement.
    """
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)
    built_in_import_modules: List[str] = []
    custom_import_modules: List[str] = []

    if module_name is None or class_name is None:
        base_service_class = measurement_service_class.split(".")[-1]
        base_service_class = _remove_suffix(base_service_class)
        if not base_service_class:
            raise click.ClickException(
                "Unable to create client.\nPlease provide valid module name or update the measurement with valid service class."
            )

        if module_name is None:
            module_name = camel_to_snake_case(base_service_class) + "_client"
        if class_name is None:
            class_name = base_service_class.title().replace("_", "") + "Client"

    if not module_name.isidentifier():
        raise click.ClickException(f"Invalid module name: '{module_name}'.")
    if not class_name.isalnum() or class_name[0].isnumeric():
        raise click.ClickException(f"Invalid class name: '{class_name}'.")

    measurement_service_stub = get_measurement_service_stub(
        discovery_client, channel_pool, measurement_service_class
    )
    metadata = measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    configuration_metadata = get_configuration_metadata_by_index(
        metadata, measurement_service_class
    )
    output_metadata = get_output_metadata_by_index(metadata)

    configuration_parameters_with_type_and_default_values, measure_api_parameters = (
        get_configuration_parameters_with_type_and_default_values(
            configuration_metadata, built_in_import_modules
        )
    )
    output_parameters_with_type = get_output_parameters_with_type(
        output_metadata, built_in_import_modules, custom_import_modules
    )

    if directory_out is None:
        directory_out_path = pathlib.Path.cwd()
    else:
        directory_out_path = pathlib.Path(directory_out)

    _create_file(
        template_name="measurement_plugin_client.py.mako",
        file_name=f"{module_name}.py",
        directory_out=directory_out_path,
        class_name=class_name,
        display_name=metadata.measurement_details.display_name,
        configuration_metadata=configuration_metadata,
        output_metadata=output_metadata,
        service_class=measurement_service_class,
        configuration_parameters_with_type_and_default_values=configuration_parameters_with_type_and_default_values,
        measure_api_parameters=measure_api_parameters,
        output_parameters_with_type=output_parameters_with_type,
        built_in_import_modules=to_ordered_set(built_in_import_modules),
        custom_import_modules=to_ordered_set(custom_import_modules),
    )

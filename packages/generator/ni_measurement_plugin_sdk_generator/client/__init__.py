"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
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
    get_all_registered_measurement_service_classes,
    is_python_identifier,
    remove_suffix,
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


@click.command()
@click.argument("measurement_service_class", nargs=-1)
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
    "-a",
    "--all",
    is_flag=True,
    help="Creates Python Measurement Plug-In Client for all the registered measurement services.",
)
@click.option(
    "-o",
    "--directory-out",
    help="Output directory for Measurement Plug-In Client files. Default: '<current_directory>/<module_name>'",
)
def create_client(
    measurement_service_class: List[str],
    all: bool,
    module_name: Optional[str],
    class_name: Optional[str],
    directory_out: Optional[str],
) -> None:
    """Generates a Python Measurement Plug-In Client module for the measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MEASUREMENT_SERVICE_CLASS: Accepts one or more measurement service classes.
    Separate each service class with a space.
    """
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)
    built_in_import_modules: List[str] = []
    custom_import_modules: List[str] = []

    if all:
        measurement_service_class = get_all_registered_measurement_service_classes(discovery_client)
        if len(measurement_service_class) == 0:
            raise click.ClickException("No registered measurements.")
    else:
        if not measurement_service_class:
            raise click.ClickException(
                "The measurement service class cannot be empty. Either provide a measurement service class or use the 'all' flag to generate clients for all registered measurements."
            )

    if directory_out is None:
        directory_out_path = pathlib.Path.cwd()
    else:
        directory_out_path = pathlib.Path(directory_out)

    if not directory_out_path.exists():
        raise click.ClickException(f"The specified directory '{directory_out}' was not found.")

    is_multiple_client_generation = len(measurement_service_class) > 1
    for service_class in measurement_service_class:
        if is_multiple_client_generation or module_name is None or class_name is None:
            base_service_class = service_class.split(".")[-1]
            base_service_class = remove_suffix(base_service_class)

            if not base_service_class.isidentifier():
                raise click.ClickException(
                    "Client creation failed.\nEither provide a module name or update the measurement with a valid service class."
                )
            if not any(ch.isupper() for ch in base_service_class):
                print(
                    f"Warning: The service class '{service_class}' does not adhere to the recommended format."
                )

            if is_multiple_client_generation:
                module_name = camel_to_snake_case(base_service_class) + "_client"
                class_name = base_service_class.replace("_", "") + "Client"
            else:
                if module_name is None:
                    module_name = camel_to_snake_case(base_service_class) + "_client"
                if class_name is None:
                    class_name = base_service_class.replace("_", "") + "Client"

        if not is_python_identifier(module_name):
            raise click.ClickException(
                f"The module name '{module_name}' is not a valid Python identifier."
            )
        if not is_python_identifier(class_name):
            raise click.ClickException(
                f"The class name '{class_name}' is not a valid Python identifier."
            )

        measurement_service_stub = get_measurement_service_stub(
            discovery_client, channel_pool, service_class
        )
        metadata = measurement_service_stub.GetMetadata(
            v2_measurement_service_pb2.GetMetadataRequest()
        )
        configuration_metadata = get_configuration_metadata_by_index(metadata, service_class)
        output_metadata = get_output_metadata_by_index(metadata)

        configuration_parameters_with_type_and_default_values, measure_api_parameters = (
            get_configuration_parameters_with_type_and_default_values(
                configuration_metadata, built_in_import_modules
            )
        )
        output_parameters_with_type = get_output_parameters_with_type(
            output_metadata, built_in_import_modules, custom_import_modules
        )

        _create_file(
            template_name="measurement_plugin_client.py.mako",
            file_name=f"{module_name}.py",
            directory_out=directory_out_path,
            class_name=class_name,
            display_name=metadata.measurement_details.display_name,
            configuration_metadata=configuration_metadata,
            output_metadata=output_metadata,
            service_class=service_class,
            configuration_parameters_with_type_and_default_values=configuration_parameters_with_type_and_default_values,
            measure_api_parameters=measure_api_parameters,
            output_parameters_with_type=output_parameters_with_type,
            built_in_import_modules=to_ordered_set(built_in_import_modules),
            custom_import_modules=to_ordered_set(custom_import_modules),
            type_url=f"type.googleapis.com/{metadata.measurement_signature.configuration_parameters_message_type}",
        )

        print(
            f"The measurement plug-in client for the service class '{service_class}' has been created successfully."
        )

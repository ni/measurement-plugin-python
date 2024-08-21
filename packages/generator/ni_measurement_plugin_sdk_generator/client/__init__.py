"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import os
import pathlib
from typing import Any, Dict, Optional

import black
import click
from mako.template import Template
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool

from ni_measurement_plugin_sdk_generator.client._constants import (
    V2_MEASUREMENT_SERVICE_INTERFACE,
)
from ni_measurement_plugin_sdk_generator.client._support import (
    get_configuration_metadata_by_index,
    get_configuration_parameters_with_type_and_default_values,
    get_measurement_service_stub,
    get_output_metadata_by_index,
    get_output_parameters_with_type,
    get_python_module_name,
)


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)
    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")

    try:
        return template.render(**template_args)
    except Exception:
        raise RuntimeError(f'An error occurred while rendering template "{template_name}".')


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args).decode("utf-8")
    formatted_output = black.format_str(
        src_contents=output,
        mode=black.Mode(line_length=100),
    )
    formatted_output = formatted_output.replace("\n", os.linesep)

    with output_file.open("wb") as file:
        file.write(formatted_output.encode("utf-8"))


@click.command()
@click.argument("module_name", type=str, default="")
@click.option(
    "-s",
    "--measurement-service-class",
    help="The service class of your measurement.",
)
@click.option(
    "-o",
    "--directory-out",
    help="Output directory for Measurement Plug-In Client files. Default: '<current_directory>/<module_name>'",
)
def create_client(
    module_name: str,
    measurement_service_class: str,
    directory_out: Optional[str],
) -> None:
    """Generates a Python Measurement Plug-In Client module for the measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MODULE_NAME: Name for the Python Measurement Plug-In Client module to be generated.
    """
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)
    import_modules: Dict[str, str] = {}

    try:
        measurement_service_stub = get_measurement_service_stub(
            discovery_client, channel_pool, measurement_service_class
        )
        registered_measurement_services = discovery_client.enumerate_services(
            V2_MEASUREMENT_SERVICE_INTERFACE
        )

        if not registered_measurement_services:
            click.ClickException(
                "No active measurements were found. Please start one and try again."
            )

        selected_measurement_service = next(
            (
                measurement_service
                for measurement_service in registered_measurement_services
                if measurement_service.service_class == measurement_service_class
            ),
            None,
        )

        if selected_measurement_service is None:
            click.ClickException(
                f"Could not find any registered measurement with service class: '{measurement_service_class}'."
            )
            return

        if not module_name.isidentifier():
            module_name = get_python_module_name(
                selected_measurement_service.service_class + "_client"
            )
        class_name = module_name.title().replace("_", "")

        metadata = measurement_service_stub.GetMetadata(
            v2_measurement_service_pb2.GetMetadataRequest()
        )
        configuration_metadata = get_configuration_metadata_by_index(
            metadata, selected_measurement_service.service_class
        )
        output_metadata = get_output_metadata_by_index(metadata)
        configuration_parameters_with_type_and_default_values, measure_api_parameters = (
            get_configuration_parameters_with_type_and_default_values(
                configuration_metadata, import_modules
            )
        )
        output_parameters_with_type = get_output_parameters_with_type(
            output_metadata, import_modules
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
            measure_docstring=selected_measurement_service.annotations["ni/service.description"],
            configuration_metadata=configuration_metadata,
            output_metadata=output_metadata,
            service_class=measurement_service_class,
            configuration_parameters_with_type_and_default_values=configuration_parameters_with_type_and_default_values,
            measure_api_parameters=measure_api_parameters,
            output_parameters_with_type=output_parameters_with_type,
            import_modules=import_modules,
        )
    except Exception as e:
        raise click.ClickException(str(e))

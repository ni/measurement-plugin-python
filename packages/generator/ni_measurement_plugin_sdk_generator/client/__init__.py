"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
from typing import Any, Dict, Optional

import black
import click
import grpc
from mako.template import Template
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool

from ni_measurement_plugin_sdk_generator.client._support import (
    get_configuration_metadata_by_index,
    get_configuration_parameters_with_type_and_default_values,
    get_measurement_service_stub,
    get_output_metadata_by_index,
    get_output_parameters_with_type,
    get_python_module_name,
    get_python_class_name,
    ImportType,
)


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)
    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")

    try:
        return template.render(**template_args)
    except Exception:
        raise click.ClickException(f'An error occurred while rendering template "{template_name}".')


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


def _get_metadata(
    discovery_client: DiscoveryClient,
    channel_pool: GrpcChannelPool,
    service_class: str,
) -> v2_measurement_service_pb2.GetMetadataResponse:
    try:
        measurement_service_stub = get_measurement_service_stub(
            discovery_client, channel_pool, service_class
        )

        metadata = measurement_service_stub.GetMetadata(
            v2_measurement_service_pb2.GetMetadataRequest()
        )
        return metadata
    except grpc.RpcError as e:
        raise click.ClickException(f"{e}")    


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
    import_modules: Dict[str, ImportType] = {}

    if module_name is None or not module_name.isidentifier():
        module_name = get_python_module_name(measurement_service_class)

    if class_name is None or not class_name.isalnum():
        class_name = get_python_class_name(measurement_service_class)

    try:
        metadata = _get_metadata(
            discovery_client, channel_pool, measurement_service_class
        )
        configuration_metadata = get_configuration_metadata_by_index(
            metadata, measurement_service_class
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
            display_name=metadata.measurement_details.display_name,
            configuration_metadata=configuration_metadata,
            output_metadata=output_metadata,
            service_class=measurement_service_class,
            configuration_parameters_with_type_and_default_values=configuration_parameters_with_type_and_default_values,
            measure_api_parameters=measure_api_parameters,
            output_parameters_with_type=output_parameters_with_type,
            import_modules=import_modules,
        )
    except TypeError as e:
        raise click.ClickException(f"{e}")
    except click.ClickException as e:
        raise click.ClickException(f"{e}")
    except Exception as e:
        raise Exception(f"Error in creating measurement plug-in client.\nPossible reasons: {e}")

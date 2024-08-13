"""Utilizes command line args to create a measurement client using template files."""

import pathlib
from typing import Any

import click
from mako.template import Template
from ni_measurement_plugin_sdk_generator.ni_measurement_plugin_client_generator._support import (
    _check_if_measurement_service_running,
    _get_configuration_metadata,
    _get_measure_output_fields_with_type,
    _get_measure_parameters_with_type_and_default_value,
    _get_measurement_service_stub,
    _get_output_metadata,
    _get_python_module_name,
    _IMPORT_MODULES,
    _V2_MEASUREMENT_SERVICE_INTERFACE,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)

def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)

    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    try:
        return template.render(**template_args)
    except Exception as e:
        raise click.ClickException(
            f'An error occurred while rendering template "{template_name}".'
        ) from e


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("wb") as fout:
        fout.write(output)


@click.command()
@click.argument("module_name", type=str, default="")
@click.option(
    "-s",
    "--measurement-service-class",
    callback=_check_if_measurement_service_running,
    help="The service class of your measurement.",
)
def create_client(module_name: str, measurement_service_class: str) -> None:
    """Generates a Python measurement client module for a measurement service from the template.

    You can use the generated module to interact with the corresponding measurement service.

    MODULE_NAME: Name for the Python measurement client module to be generated.
    """
    discovery_client = DiscoveryClient()
    registered_measurement_services = discovery_client.enumerate_services(_V2_MEASUREMENT_SERVICE_INTERFACE)

    if not registered_measurement_services:
        print("No active measurements were found. Please start one and try again.")
        return

    if not measurement_service_class:
        raise Exception("Invalid input : Please try again with a valid measurement service class.")
    
    selected_measurement_service = next(
        measurement_service
        for measurement_service in registered_measurement_services
        if measurement_service.service_class == measurement_service_class
    )

    if not module_name:
        module_name = _get_python_module_name(selected_measurement_service.display_name)
    
    measurement_service_stub  = _get_measurement_service_stub(discovery_client, measurement_service_class)
    metadata = measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())


    configuration_metadata = _get_configuration_metadata(metadata, selected_measurement_service.service_class)
    output_metadata = _get_output_metadata(metadata)

    measure_parameters_with_type, measure_param_names, enum_values_by_type_name = (
        _get_measure_parameters_with_type_and_default_value(configuration_metadata)
    )
    measure_return_values_with_type = _get_measure_output_fields_with_type(
        output_metadata, enum_values_by_type_name
    )

    directory_out_path = pathlib.Path.cwd() / module_name
    directory_out_path.mkdir(exist_ok=True, parents=True)

    _create_file(
        template_name="_helpers.py.mako",
        file_name="_helpers.py",
        directory_out=directory_out_path,
        measure_return_values_with_type=measure_return_values_with_type,
        output_metadata=output_metadata,
        enum_by_class_name=enum_values_by_type_name,
    )

    _create_file(
        template_name="measurement_plugin_client.py.mako",
        file_name=f"{module_name}.py",
        directory_out=directory_out_path,
        measure_docstring=selected_measurement_service.annotations["ni/service.description"],
        configuration_metadata=configuration_metadata,
        output_metadata=output_metadata,
        service_class=measurement_service_class,
        measure_parameters_with_type=measure_parameters_with_type,
        measure_parameters=measure_param_names,
        enum_by_class_name=enum_values_by_type_name,
        measure_return_values_with_type=measure_return_values_with_type,
        import_modules = _IMPORT_MODULES,
    )
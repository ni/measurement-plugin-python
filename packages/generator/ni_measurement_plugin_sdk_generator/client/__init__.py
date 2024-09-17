"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Type

import black
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from mako.template import Template
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool

from ni_measurement_plugin_sdk_generator.client._support import (
    create_class_name,
    create_module_name,
    extract_base_service_class,
    get_configuration_metadata_by_index,
    get_configuration_parameters_with_type_and_default_values,
    get_measurement_service_stub,
    get_output_metadata_by_index,
    get_output_parameters_with_type,
    get_all_registered_measurement_info,
    get_selected_measurement_service_class,
    to_ordered_set,
    resolve_output_directory,
    validate_identifier,
    validate_measurement_service_classes,
)


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)
    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    return template.render(**template_args)


def _replace_enum_class_type(output: str) -> str:
    pattern = "<enum '([^']+)'>"
    return re.sub(pattern, r"\1", output)


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args).decode("utf-8")
    output = _replace_enum_class_type(output)
    formatted_output = black.format_str(
        src_contents=output,
        mode=black.Mode(line_length=100),
    )

    with output_file.open("w") as file:
        file.write(formatted_output)


def _create_client(
    discovery_client: DiscoveryClient,
    channel_pool: GrpcChannelPool,
    measurement_service_class: str,
    module_name: str,
    class_name: str,
    directory_out: pathlib.Path,
) -> None:
    built_in_import_modules: List[str] = []
    custom_import_modules: List[str] = []
    enum_values_by_type: Dict[Type[Enum], Dict[str, int]] = {}

    measurement_service_stub = get_measurement_service_stub(
        discovery_client, channel_pool, measurement_service_class
    )
    metadata = measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    configuration_metadata = get_configuration_metadata_by_index(
        metadata, measurement_service_class, enum_values_by_type
    )
    output_metadata = get_output_metadata_by_index(metadata, enum_values_by_type)

    configuration_parameters_with_type_and_default_values, measure_api_parameters = (
        get_configuration_parameters_with_type_and_default_values(
            configuration_metadata, built_in_import_modules, enum_values_by_type
        )
    )
    output_parameters_with_type = get_output_parameters_with_type(
        output_metadata, built_in_import_modules, custom_import_modules, enum_values_by_type
    )

    _create_file(
        template_name="measurement_plugin_client.py.mako",
        file_name=f"{module_name}.py",
        directory_out=directory_out,
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
        enum_by_class_name=enum_values_by_type,
    )

    print(
        f"The measurement plug-in client for the service class '{measurement_service_class}' is created successfully."
    )


def _create_all_clients(directory_out: Optional[str]) -> None:
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)

    directory_out_path = resolve_output_directory(directory_out)
    measurement_service_classes, _ = get_all_registered_measurement_info(discovery_client)
    validate_measurement_service_classes(measurement_service_classes)

    for service_class in measurement_service_classes:
        base_service_class = extract_base_service_class(service_class)
        module_name = create_module_name(base_service_class)
        class_name = create_class_name(base_service_class)
        validate_identifier(module_name, "module")
        validate_identifier(class_name, "class")

        _create_client(
            channel_pool=channel_pool,
            discovery_client=discovery_client,
            measurement_service_class=service_class,
            module_name=module_name,
            class_name=class_name,
            directory_out=directory_out_path,
        )


def _create_clients_interactively() -> None:
    print("Creating the Python Measurement Plug-In Client in interactive mode...")
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)
    directory_out_path = resolve_output_directory()

    while True:
        measurement_service_classes, measurement_display_names = (
            get_all_registered_measurement_info(discovery_client)
        )
        validate_measurement_service_classes(measurement_service_classes)

        print("\nList of registered measurements:")
        for index, display_name in enumerate(measurement_display_names, start=1):
            print(f"{index}. {display_name}")

        selection = click.prompt(
            "\nSelect a measurement to generate a client (x to exit)",
            type=str,
        )
        if selection.lower() == "x":
            break
        service_class = get_selected_measurement_service_class(
            int(selection), measurement_service_classes
        )

        base_service_class = extract_base_service_class(service_class)
        default_module_name = create_module_name(base_service_class)
        module_name = click.prompt(
            "Enter a name for the Python client module, or press Enter to use the default name.",
            type=str,
            default=default_module_name,
        )
        validate_identifier(module_name, "module")
        default_class_name = create_class_name(base_service_class)
        class_name = click.prompt(
            "Enter a name for the Python client class, or press Enter to use the default name.",
            type=str,
            default=default_class_name,
        )
        validate_identifier(class_name, "class")

        _create_client(
            channel_pool=channel_pool,
            discovery_client=discovery_client,
            measurement_service_class=service_class,
            module_name=module_name,
            class_name=class_name,
            directory_out=directory_out_path,
        )


def _create_clients(
    measurement_service_classes: List[str],
    module_name: Optional[str],
    class_name: Optional[str],
    directory_out: Optional[str],
) -> None:
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)
    directory_out_path = resolve_output_directory(directory_out)

    has_multiple_service_classes = len(measurement_service_classes) > 1
    for service_class in measurement_service_classes:
        base_service_class = extract_base_service_class(service_class)
        if has_multiple_service_classes or module_name is None:
            module_name = create_module_name(base_service_class)
        if has_multiple_service_classes or class_name is None:
            class_name = create_class_name(base_service_class)
        validate_identifier(module_name, "module")
        validate_identifier(class_name, "class")

        _create_client(
            channel_pool=channel_pool,
            discovery_client=discovery_client,
            measurement_service_class=service_class,
            module_name=module_name,
            class_name=class_name,
            directory_out=directory_out_path,
        )


@click.command()
@optgroup.group(
    "all-modes",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="The different modes to create Python measurement client.",
)
@optgroup.option(
    "-s",
    "--measurement-service-class",
    help="Creates Python Measurement Plug-In Client for the given measurement services.",
    multiple=True,
)
@optgroup.option(
    "-a",
    "--all",
    is_flag=True,
    help="Creates Python Measurement Plug-In Clients for all registered measurement services.",
)
@optgroup.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Creates Python Measurement Plug-In Clients interactively.",
)
@optgroup.group(
    "optional parameters",
    help="Recommended parameters when using measurement service class mode.",
)
@optgroup.option(
    "-m",
    "--module-name",
    help="Name for the Python Measurement Plug-In Client module.",
)
@optgroup.option(
    "-c",
    "--class-name",
    help="Name for the Python Measurement Plug-In Client Class in the generated module.",
)
@optgroup.option(
    "-o",
    "--directory-out",
    help="Output directory for Measurement Plug-In Client files. Default: '<current_directory>/<module_name>'",
)
def create_client(
    measurement_service_class: List[str],
    all: bool,
    interactive: bool,
    module_name: Optional[str],
    class_name: Optional[str],
    directory_out: Optional[str],
) -> None:
    """Generates a Python Measurement Plug-In Client module for the measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MEASUREMENT_SERVICE_CLASS: Accepts one or more measurement service classes.
    Provide each service class separately.
    """
    if all:
        _create_all_clients(directory_out)
    elif interactive:
        _create_clients_interactively()
    else:
        _create_clients(
            measurement_service_classes=measurement_service_class,
            module_name=module_name,
            class_name=class_name,
            directory_out=directory_out,
        )

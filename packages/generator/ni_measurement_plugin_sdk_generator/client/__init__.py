"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
from typing import Any, List, Optional

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
    camel_to_snake_case,
    get_configuration_metadata_by_index,
    get_configuration_parameters_with_type_and_default_values,
    get_measurement_service_stub,
    get_output_metadata_by_index,
    get_output_parameters_with_type,
    get_all_registered_measurement_info,
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


def _resolve_output_directory(directory_out: Optional[str] = None) -> pathlib.Path:
    if directory_out is None:
        directory_out_path = pathlib.Path.cwd()
    else:
        directory_out_path = pathlib.Path(directory_out)

    if not directory_out_path.exists():
        raise click.ClickException(f"The specified directory '{directory_out}' was not found.")

    return directory_out_path


def _validate_identifier(name: str, name_type: str) -> None:
    if not is_python_identifier(name):
        raise click.ClickException(
            f"The {name_type} name '{name}' is not a valid Python identifier."
        )


def _extract_base_service_class(service_class: str) -> str:
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
    return base_service_class


def _create_module_name(base_service_class: str) -> str:
    return camel_to_snake_case(base_service_class) + "_client"


def _create_class_name(base_service_class: str) -> str:
    return base_service_class.replace("_", "") + "Client"


def _get_selected_measurement_service_class(
    selection: int, measurement_service_classes: List[str]
) -> List[str]:
    if not (1 <= selection <= len(measurement_service_classes)):
        raise click.ClickException(
            f"Input {selection} is not invalid. Please try again by selecting a valid measurement from the list."
        )
    return measurement_service_classes[selection - 1]


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
    )

    print(
        f"The measurement plug-in client for the service class '{measurement_service_class}' has been created successfully."
    )


@click.command()
@optgroup.group(
    "all-modes",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="The different modes to create Python measurement client.",
)
@optgroup.option(
    "-s",
    "--measurement_service_class",
    help="Creates Python Measurement Plug-In Client for the given measurement services.",
    multiple=True,
)
@optgroup.option(
    "-a",
    "--all",
    is_flag=True,
    help="Creates Python Measurement Plug-In Client for all the registered measurement services.",
)
@optgroup.option(
    "-i",
    "--interactive",
    is_flag=True,
    help=(
        "Creates Python Measurement Plug-In Client for any registered measurement services interactively."
    ),
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
    module_name: Optional[str],
    class_name: Optional[str],
    directory_out: Optional[str],
    interactive: bool,
) -> None:
    """Generates a Python Measurement Plug-In Client module for the measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MEASUREMENT_SERVICE_CLASS: Accepts one or more measurement service classes.
    Separate each service class with a space.
    """
    channel_pool = GrpcChannelPool()
    discovery_client = DiscoveryClient(grpc_channel_pool=channel_pool)

    if all:
        directory_out = _resolve_output_directory(directory_out)
        measurement_service_class, _ = get_all_registered_measurement_info(discovery_client)
        if len(measurement_service_class) == 0:
            raise click.ClickException("No registered measurements.")
        
        for service_class in measurement_service_class:
            base_service_class = _extract_base_service_class(service_class)
            module_name = _create_module_name(base_service_class)
            class_name = _create_class_name(base_service_class)
            _validate_identifier(module_name, "module")
            _validate_identifier(class_name, "class")

            _create_client(
                channel_pool=channel_pool,
                discovery_client=discovery_client,
                measurement_service_class=service_class,
                module_name=module_name,
                class_name=class_name,
                directory_out=directory_out,
            )

    elif interactive:
        print("Creating the Python Measurement Plug-In Client in interactive mode...")
        directory_out = _resolve_output_directory()

        while True:
            measurement_service_class, measurement_display_names = (
                get_all_registered_measurement_info(discovery_client)
            )
            if len(measurement_service_class) == 0:
                raise click.ClickException("No registered measurements.")

            print("\nList of registered measurements:")
            for index, display_name in enumerate(measurement_display_names, start=1):
                print(f"{index}. {display_name}")

            selection = click.prompt(
                "\nSelect a measurement to generate a client",
                type=int,
            )
            service_class = _get_selected_measurement_service_class(
                selection, measurement_service_class
            )

            base_service_class = _extract_base_service_class(service_class)
            default_module_name = _create_module_name(base_service_class)
            module_name = click.prompt(
                "Enter a name for the Python client module (or) press enter to choose the default name",
                type=str,
                default=default_module_name,
            )
            _validate_identifier(module_name, "module")
            default_class_name = _create_class_name(base_service_class)
            class_name = click.prompt(
                "Enter a name for the Python client class (or) press enter to choose the default name",
                type=str,
                default=default_class_name,
            )
            _validate_identifier(class_name, "class")

            _create_client(
                channel_pool=channel_pool,
                discovery_client=discovery_client,
                measurement_service_class=service_class,
                module_name=module_name,
                class_name=class_name,
                directory_out=directory_out,
            )

            selection = (
                click.prompt(
                    "\nEnter 'x' to exit or enter any other keys to continue client creation for another measurement",
                    type=str,
                    default="x",
                    show_default=False,
                )
                .strip()
                .lower()
            )
            if selection == "x":
                break
    else:
        if not measurement_service_class:
            raise click.ClickException(
                "The measurement service class cannot be empty. Please provide a measurement service class or use the 'all' flag to generate clients for all registered measurements or 'interactive' flag to generate client for any registered measurements."
            )
        directory_out = _resolve_output_directory(directory_out)

        for service_class in measurement_service_class:
            base_service_class = _extract_base_service_class(service_class)
            if module_name is None:
                module_name = _create_module_name(base_service_class)
            if class_name is None:
                class_name = _create_class_name(base_service_class)
            _validate_identifier(module_name, "module")
            _validate_identifier(class_name, "class")

            _create_client(
                channel_pool=channel_pool,
                discovery_client=discovery_client,
                measurement_service_class=service_class,
                module_name=module_name,
                class_name=class_name,
                directory_out=directory_out,
            )

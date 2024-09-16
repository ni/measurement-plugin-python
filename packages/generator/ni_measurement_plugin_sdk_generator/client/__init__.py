"""Utilizes command line args to create a Measurement Plug-In Client using template files."""

import pathlib
from typing import Any, List, Optional, Tuple

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


def _resolve_output_directory(directory_out: Optional[str]) -> pathlib.Path:
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


def _get_interactive_module_and_class_names(base_service_class: str) -> Tuple[str, str]:
    default_module_name = _create_module_name(base_service_class)
    module_name = click.prompt("Enter a name for the Python client module (or) press enter to choose the default name", type=str, default=default_module_name)
    _validate_identifier(module_name, "module")

    default_class_name = _create_class_name(base_service_class)
    class_name = click.prompt("Enter a name for the Python client class (or) press enter to choose the default name", type=str, default=default_class_name)
    _validate_identifier(class_name, "class")

    return module_name, class_name


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


def _get_class_and_module_names(
    service_class: str,
    is_multiple_client_generation: bool,
    module_name: Optional[str],
    class_name: Optional[str],
    interactive_mode: bool,
) -> Tuple[str, str]:
    base_service_class = _extract_base_service_class(service_class)
    if interactive_mode:
        return _get_interactive_module_and_class_names(base_service_class)
    elif is_multiple_client_generation or module_name is None or class_name is None:
        if is_multiple_client_generation:
            module_name = _create_module_name(base_service_class)
            class_name = _create_class_name(base_service_class)
        else:
            if module_name is None:
                module_name = _create_module_name(base_service_class)
            if class_name is None:
                class_name = _create_class_name(base_service_class)

        _validate_identifier(module_name, "module")
        _validate_identifier(class_name, "class")
    return module_name, class_name


def _get_selected_measurement_service_class(
    selection: int, measurement_service_classes: List[str]
) -> List[str]:
    if not (1 <= selection <= len(measurement_service_classes)):
        raise click.ClickException(
            f"Input {selection} is not invalid. Please try again by selecting a valid measurement from the list."
        )
    return [measurement_service_classes[selection - 1]]


def _get_measurement_service_class(
    all: bool,
    interactive: bool,
    measurement_service_class: List[str],
    discovery_client: DiscoveryClient,
) -> List[str]:

    if all or interactive:
        measurement_service_class, measurement_display_name = get_all_registered_measurement_info(discovery_client)
        if len(measurement_service_class) == 0:
            raise click.ClickException("No registered measurements.")
        if interactive:
            print("\nList of registered measurements:")
            for index, service_class in enumerate(measurement_display_name, start=1):
                print(f"{index}. {service_class}")

            selection = click.prompt(
                "\nSelect a measurement to generate a client",
                type=int,
            )
            measurement_service_class = _get_selected_measurement_service_class(
                selection, measurement_service_class
            )

    else:
        if not measurement_service_class:
            raise click.ClickException(
                "The measurement service class cannot be empty. Either provide a measurement service class or use the 'all' flag to generate clients for all registered measurements."
            )
    return measurement_service_class


def _generate_measurement_client(
    discovery_client: DiscoveryClient,
    channel_pool: GrpcChannelPool,
    service_class: str,
    module_name: str,
    class_name: str,
    directory_out_path: pathlib.Path,
) -> None:
    built_in_import_modules: List[str] = []
    custom_import_modules: List[str] = []

    measurement_service_stub = get_measurement_service_stub(
        discovery_client, channel_pool, service_class
    )
    metadata = measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
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
    )

    print(
        f"The measurement plug-in client for the service class '{service_class}' has been created successfully."
    )


def _create_client(
    channel_pool: GrpcChannelPool,
    discovery_client: DiscoveryClient,
    measurement_service_class: List[str] = [],
    all: bool = False,
    module_name: Optional[str] = None,
    class_name: Optional[str] = None,
    directory_out: Optional[str] = "",
    interactive_mode: bool = False,
) -> None:

    measurement_service_class = _get_measurement_service_class(
        all, interactive_mode, measurement_service_class, discovery_client
    )

    directory_out_path = _resolve_output_directory(directory_out)

    is_multiple_client_generation = len(measurement_service_class) > 1
    for service_class in measurement_service_class:
        module_name, class_name = _get_class_and_module_names(
            service_class, is_multiple_client_generation, module_name, class_name, interactive_mode
        )
        _generate_measurement_client(
            discovery_client,
            channel_pool,
            service_class,
            module_name,
            class_name,
            directory_out_path,
        )


@click.command()
@click.argument("measurement_service_class", nargs=-1)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Creates Python Measurement Plug-In Client for all the registered measurement services.",
)
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
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help=(
        "Enables interactive mode for creating Measurement Plug-In Client files. "
        "If no parameters are provided, this mode will be activated by default. "
        "When using this mode, no other parameters should be specified. "
    ),
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

    has_batch_parameters = (
        measurement_service_class or all or module_name or class_name or directory_out
    )
    if has_batch_parameters and not interactive:
        _create_client(
            channel_pool=channel_pool,
            discovery_client=discovery_client,
            measurement_service_class=measurement_service_class,
            all=all,
            module_name=module_name,
            class_name=class_name,
            directory_out=directory_out,
        )
    else:
        if has_batch_parameters and interactive:
            raise click.ClickException(
                "Interactive mode does not support additional parameters. Please remove any extra parameters and try again."
            )
        print("Creating the Python Measurement Plug-In Client in interactive mode...")
        while True:
            _create_client(
                channel_pool=channel_pool,
                discovery_client=discovery_client,
                interactive_mode=True,
            )

            selection = (
                click.prompt(
                    "\nEnter 'yes' or 'y' to continue, or enter any other keys to exit",
                    type=str,
                    default="",
                    show_default=False,
                )
                .strip()
                .lower()
            )
            if selection in ["yes", "y"]:
                continue
            else:
                break

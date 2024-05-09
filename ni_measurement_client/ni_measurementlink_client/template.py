"""Python measurement client template generator."""

import json
import keyword
import pathlib
from typing import Any, Dict, Optional, Sequence, Tuple

import click
import grpc
from google.protobuf.type_pb2 import Field
from mako.template import Template
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.parameter.serializer import (
    deserialize_parameters,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.discovery import DiscoveryClient, ServiceDescriptor

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
_PROTO_DATATYPE_TO_PYTYPE_LOOKUP = {
    Field.TYPE_INT32: int,
    Field.TYPE_INT64: int,
    Field.TYPE_UINT32: int,
    Field.TYPE_UINT64: int,
    Field.TYPE_SINT32: int,
    Field.TYPE_SINT64: int,
    Field.TYPE_FIXED32: int,
    Field.TYPE_FIXED64: int,
    Field.TYPE_SFIXED32: int,
    Field.TYPE_SFIXED64: int,
    Field.TYPE_FLOAT: float,
    Field.TYPE_DOUBLE: float,
    Field.TYPE_BOOL: bool,
    Field.TYPE_STRING: str,
    Field.TYPE_ENUM: int,
}
_INVALID_CHARS = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n"


def _check_if_measurement_service_running(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> str:
    try:
        if service_class:
            DiscoveryClient().resolve_service(_V2_MEASUREMENT_SERVICE_INTERFACE, service_class)
        return service_class
    except Exception:
        raise click.BadParameter(
            f"Could not find any active measurement with service class: '{service_class}'."
        )


def _get_measurement_service_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _get_module_name_and_service_class(
    available_measurement_services: Sequence[ServiceDescriptor],
) -> Tuple[str, str]:
    print("List of available measurements: ")
    for i, service in enumerate(available_measurement_services):
        print(f"{i+1}. {service.display_name}")

    try:
        index = int(
            input(
                "\nEnter the serial number for the desired measurement service client creation: "
            )
        )
    except Exception:
        raise Exception("Invalid input. Please try again by entering a valid serial number.")

    if 0 <= index > len(available_measurement_services):
        raise Exception("Input out of bounds. Please try again by entering a valid serial number.")

    measurement_service_class = available_measurement_services[index - 1].service_class
    module_name = input("Please provide the name for the measurement client module: ")
    return (module_name, measurement_service_class)


def _get_configuration_metadata_by_id(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    configuration_metadata_by_id = {}
    for configuration in metadata.measurement_signature.configuration_parameters:
        configuration_metadata_by_id[configuration.field_number] = ParameterMetadata(
            configuration.name,
            configuration.type,
            configuration.repeated,
            0,
            configuration.annotations,
            configuration.message_type,
        )

    params = deserialize_parameters(
        configuration_metadata_by_id, metadata.measurement_signature.configuration_defaults.value
    )
    default_values = [None] * params.__len__()
    for k, v in params.items():
        configuration_metadata_by_id[k] = configuration_metadata_by_id[k]._replace(default_value=v)
        default_values[k - 1] = v

    return configuration_metadata_by_id


def _get_output_metadata_by_id(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    output_metadata_by_id = {}
    for output in metadata.measurement_signature.outputs:
        output_metadata_by_id[output.field_number] = ParameterMetadata(
            output.name,
            output.type,
            output.repeated,
            0,
            output.annotations,
            output.message_type,
        )

    return output_metadata_by_id


def _get_python_identifier(name: str) -> str:
    var_name = name.lower()

    # Replace any spaces or special characters with an '_'.
    if not var_name.isidentifier():
        for ch in _INVALID_CHARS:
            var_name = var_name.replace(ch, "_")

    # Python identifiers cannot begin with an integer. So prefix '_' if it does.
    if var_name[0].isdigit():
        var_name = "_" + var_name

    # Check and append a '_' if the name resembles a python keyword.
    if keyword.iskeyword(var_name):
        var_name = var_name + "_"

    return var_name

def _get_python_class_name(name: str) -> str:
    class_name = name.replace("_", " ").title().replace(" ", "")

    # Replace any spaces or special characters with an '_'.
    if not class_name.isidentifier():
        for ch in _INVALID_CHARS:
            class_name = class_name.replace(ch, "")

    # Python identifiers cannot begin with an integer. So prefix '_' if it does.
    if class_name[0].isdigit():
        class_name = "_" + class_name

    return class_name + "Enum"


def _get_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    py_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)
    if py_type is None:
        raise Exception(f"Some data types for config or output parameters are unsupported.")
    if is_array:
        return f"List[{py_type.__name__}]"
    else:
        return py_type.__name__


def _get_enum_values(parameter_metadata: ParameterMetadata) -> Dict[str, Any]:
    enum_values_in_json = parameter_metadata.annotations["ni/enum.values"]
    enum_values: Dict[str, Any] = json.loads(enum_values_in_json)

    # Replace any spaces or special characters with an '_'.
    pythonic_enum_values : Dict[str, Any] = {}
    for k, v in enum_values.items():
        for ch in _INVALID_CHARS:
            k = k.replace(ch, "")

        # Python identifiers cannot begin with an integer. So prefix '_' if it does.
        if k[0].isdigit():
            k = "_" + k

        pythonic_enum_values[k] = v

    return pythonic_enum_values


def _get_measure_parameters_with_type_and_default_value(
    configuration_metadata_by_id: Dict[int, ParameterMetadata]
) -> Tuple[str, str, Dict[str, Dict[str, Any]]]:
    method_params_with_type_and_value = []
    parameter_names = []
    enum_values_by_name: Dict[str, Dict[str, Any]] = dict()
    for metadata in configuration_metadata_by_id.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_names.append(parameter_name)

        default_value = metadata.default_value
        if isinstance(default_value, str):
            default_value = f'"{default_value}"'

            # If it's path type, make the value as raw string literal to ignore escape characters.
            if metadata.annotations and metadata.annotations["ni/type_specialization"] == "path":
                default_value = f'r{default_value}'

        param_type = _get_python_type_as_str(metadata.type, metadata.repeated)
        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_values = _get_enum_values(metadata)
            enum_type_name = _get_python_class_name(metadata.display_name)
            enum_values_by_name[enum_type_name] = enum_values
            enum_value = next(key for key, val in enum_values.items() if val == default_value)
            method_params_with_type_and_value.append(
                f"{parameter_name}: {enum_type_name} = {enum_type_name}.{enum_value}"
            )
        else:
            method_params_with_type_and_value.append(f"{parameter_name}: {param_type} = {default_value}")

    # Use newline and spaces to align the method parameters appropriately in the generated file.
    method_parameters_with_type_and_value = ",\n    ".join(method_params_with_type_and_value)
    parameter_names_as_str = ",\n        ".join(parameter_names)

    return (method_parameters_with_type_and_value, parameter_names_as_str, enum_values_by_name)


def _get_measure_output_fields_with_type(
    output_metadata_by_id: Dict[int, ParameterMetadata],
    enum_values_by_type_name: Dict[str, Dict[str, Any]],
) -> str:
    output_names_with_type = []
    for metadata in output_metadata_by_id.values():
        param_name = _get_python_identifier(metadata.display_name)

        param_type = _get_python_type_as_str(metadata.type, metadata.repeated)
        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_values_dict: Dict[str, Any] = _get_enum_values(metadata)
            for enum_name, enum_dict in enum_values_by_type_name.items():
                if enum_values_dict == enum_dict:
                    param_type = enum_name

        output_names_with_type.append(f"{param_name}: {param_type}")

    return "\n    ".join(output_names_with_type)


def _add_default_values_for_output_enum_parameters(
    output_metadata_by_id: Dict[int, ParameterMetadata],
    enum_values_by_name: Dict[str, Dict[str, Any]],
) -> None:
    for key, metadata in output_metadata_by_id.items():
        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_values_dict: Dict[str, Any] = _get_enum_values(metadata)
            for enum_name, values in enum_values_by_name.items():
                if enum_values_dict == values:
                    output_metadata_by_id[key] = output_metadata_by_id[key]._replace(
                        default_value=f"{enum_name}.{list(values.keys())[0]}"
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
    "-m",
    "--measurement-service-class",
    callback=_check_if_measurement_service_running,
    help="The service class of your measurement.",
)
@click.option(
    "-i",
    "--interactive-mode",
    is_flag=True,
    help="Utilize interactive input for Python measurement client creation.",
)
def create_client(
    module_name: str, measurement_service_class: Optional[str], interactive_mode: bool
) -> None:
    """Generates a Python measurement client module for a measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    MODULE_NAME: Name for the generated Python measurement client module.
    """
    discovery_client = DiscoveryClient()
    available_measurement_services = discovery_client.enumerate_services(
        _V2_MEASUREMENT_SERVICE_INTERFACE
    )

    if not available_measurement_services:
        print("Could find any active measurements. Please start one and try again.")
        return

    if interactive_mode:
        module_name, measurement_service_class = _get_module_name_and_service_class(
            available_measurement_services
        )

    if not module_name or not module_name.isidentifier():
        raise Exception("Module name must follow Python module conventions and cannot be empty.")

    if not measurement_service_class:
        raise Exception("Invalid input. Please try again with a valid measurement service class.")

    selected_service_description = next(
        meas_service.annotations["ni/service.description"]
        for meas_service in available_measurement_services
        if meas_service.service_class == measurement_service_class
    )

    stub = _get_measurement_service_stub(discovery_client, measurement_service_class)
    metadata = stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    configuration_metadata_by_id = _get_configuration_metadata_by_id(metadata)
    output_metadata_by_id = _get_output_metadata_by_id(metadata)

    measure_parameters_with_type, measure_param_names, enum_values_by_type_name = (
        _get_measure_parameters_with_type_and_default_value(configuration_metadata_by_id)
    )
    measure_return_values_with_type = _get_measure_output_fields_with_type(
        output_metadata_by_id, enum_values_by_type_name
    )

    _add_default_values_for_output_enum_parameters(output_metadata_by_id, enum_values_by_type_name)

    directory_out_path = pathlib.Path.cwd() / module_name
    directory_out_path.mkdir(exist_ok=True, parents=True)

    _create_file(
        "measurement_client.py.mako",
        f"{module_name}.py",
        directory_out_path,
        measure_docstring=selected_service_description,
        configuration_metadata=configuration_metadata_by_id,
        output_metadata=output_metadata_by_id,
        service_class=measurement_service_class,
        measure_parameters_with_type=measure_parameters_with_type,
        measure_parameters=measure_param_names,
        enum_by_class_name=enum_values_by_type_name,
        measure_return_values_with_type=measure_return_values_with_type,
    )
    _create_file("pyproject.toml.mako",
        "pyproject.toml",
        directory_out_path,
        module_name=module_name,
        description=selected_service_description,
    )

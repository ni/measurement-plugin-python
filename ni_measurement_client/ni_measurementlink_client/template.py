"""Python measurement client template generator."""

import json
import pathlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

import click
import grpc
from google.protobuf.type_pb2 import Field
from mako.template import Template

from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.parameter.serializer import (
    deserialize_parameters,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.discovery.v1.discovery_service_pb2 import ServiceDescriptor
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.discovery import DiscoveryClient

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
_PROTO_DATATYPE_TO_PYTYPE_LOOKUP = {
    Field.Kind.TYPE_ENUM: int,
    Field.Kind.TYPE_INT32: int,
    Field.Kind.TYPE_INT64: int,
    Field.Kind.TYPE_UINT32: int,
    Field.Kind.TYPE_UINT64: int,
    Field.Kind.TYPE_FIXED32: int,
    Field.Kind.TYPE_FIXED64: int,
    Field.Kind.TYPE_FLOAT: float,
    Field.Kind.TYPE_DOUBLE: float,
    Field.Kind.TYPE_BOOL: bool,
    Field.Kind.TYPE_STRING: str,
}


def _check_measurement_service(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> str:
    try:
        if service_class:
            DiscoveryClient().resolve_service(_V2_MEASUREMENT_SERVICE_INTERFACE, service_class)
        return service_class
    except Exception:
        raise click.BadParameter(
            f"Error while resolving the measurement service with service class: {service_class}."
        )


def _get_measurement_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _get_user_inputs(available_measurement_services: Sequence[ServiceDescriptor]) -> Tuple[str, str]:
        print("List of active measurements: ")
        for i, service in enumerate(available_measurement_services):
            print(f"{i+1}. {service.display_name}")

        try:
            index = int(
                input(
                    "\nPlease enter the serial number of the measurement service that you wish to create a client for: "
                )
            )
        except Exception:
            return

        if 0 >= index > len(available_measurement_services):
            print("The input is invalid.")

        measurement_service_class = available_measurement_services[index - 1].service_class
        package_name = input("Please provide the name for the measurement client package: ")
        return (package_name, measurement_service_class)


def _deserialize_configuration_parameters(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Tuple[Dict[int, ParameterMetadata], List[Any]]:
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
    values = [None] * params.__len__()
    for k, v in params.items():
        configuration_metadata_by_id[k] = configuration_metadata_by_id[k]._replace(default_value=v)
        values[k - 1] = v

    return (configuration_metadata_by_id, values)


def _deserialize_output_parameters(
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


def _get_measure_parameters_with_type(configuration_metadata_by_id: Dict[int, ParameterMetadata], default_values: List[Any])-> Tuple[str, str, Dict[str, Dict[str, Any]]]:
    method_params_with_type = []
    param_names = []
    enums_by_class : Dict[str, Dict[str, Any]] = dict()
    for i in range(configuration_metadata_by_id.__len__()):
        enum_name = configuration_metadata_by_id[i + 1].display_name.replace("_", " ")
        enum_name = enum_name.title().replace(" ", "")
        enum_name = enum_name + "Enum"
        param_name = configuration_metadata_by_id[i + 1].display_name.lower()
        if not param_name.isidentifier():
            if param_name.__contains__(" "):
                param_name = param_name.replace(" ", "_")
            else:
                param_name = param_name + "1"
        param_type = ""
        py_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(configuration_metadata_by_id[i + 1].type)
        if py_type is None:
            raise Exception(
                f"Data type information not found '{configuration_metadata_by_id[i+1].type}'"
            )

        if configuration_metadata_by_id[i + 1].repeated:
            param_type = f"List[{py_type.__name__}]"
        else:
            param_type = py_type.__name__

        param_names.append(param_name)
        default_value = default_values[i]
        if isinstance(default_value, str):
            default_value = f'"{default_value}"'

        if configuration_metadata_by_id[i+1].annotations and configuration_metadata_by_id[i+1].annotations["ni/type_specialization"] == "enum":
            enum_values_in_json = configuration_metadata_by_id[i+1].annotations["ni/enum.values"]
            enum_values_dict : Dict[str, Any] = json.loads(enum_values_in_json)
            enums_by_class[enum_name] = enum_values_dict
            method_params_with_type.append(f"{param_name}: {enum_name} = {enum_name}.{next(key for key, val in enum_values_dict.items() if val == default_value)}")
        else:
            method_params_with_type.append(f"{param_name}: {param_type} = {default_value}")

    method_signature = ",\n\t".join(method_params_with_type)
    params_names_as_str = ",\n\t\t".join(param_names)
    return method_signature, params_names_as_str, enums_by_class


def _get_measure_return_fields_with_type(output_metadata_by_id: Dict[int, ParameterMetadata], enums_by_class: Dict[str, Dict[str, Any]]):
    output_names_with_type = []
    for i in range(output_metadata_by_id.__len__()):
        param_name = output_metadata_by_id[i + 1].display_name.lower()
        if not param_name.isidentifier():
            if param_name.__contains__(" "):
                param_name = param_name.replace(" ", "_")
            else:
                param_name = param_name + "1"
        param_type = ""
        py_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(output_metadata_by_id[i + 1].type)
        if py_type is None:
            raise Exception(
                f"Data type information not found '{output_metadata_by_id[i+1].type}'"
            )

        if output_metadata_by_id[i + 1].repeated:
            param_type = f"List[{py_type.__name__}]"
        else:
            param_type = py_type.__name__

        if output_metadata_by_id[i+1].annotations and output_metadata_by_id[i+1].annotations["ni/type_specialization"] == "enum":
            enum_values_in_json = output_metadata_by_id[i+1].annotations["ni/enum.values"]
            enum_values_dict : Dict[str, Any] = json.loads(enum_values_in_json)
            for enum_name, enum_dict in enums_by_class.items():
                if enum_values_dict == enum_dict:
                    param_type = enum_name

        output_names_with_type.append(f"{param_name}: {param_type}")

    return_values_with_type = "\n    ".join(output_names_with_type)
    return return_values_with_type


def _update_enum_default_values(configuration_metadata_by_id: Dict[int, ParameterMetadata], output_metadata_by_id: Dict[int, ParameterMetadata], enums_by_class: Dict[str, Dict[str, Any]]):
    for key, config_data in output_metadata_by_id.items():
        if config_data.annotations and config_data.annotations["ni/type_specialization"] == "enum":
            enum_values_in_json = config_data.annotations["ni/enum.values"]
            enum_values_dict : Dict[str, Any] = json.loads(enum_values_in_json)
            for enum_name, enum_dict in enums_by_class.items():
                if enum_values_dict == enum_dict:
                    output_metadata_by_id[key] = output_metadata_by_id[key]._replace(default_value=f"{enum_name}.{list(enum_dict.keys())[0]}")


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
@click.argument("package_name", type=str, default="")
@click.option(
    "-m",
    "--measurement-service-class",
    callback=_check_measurement_service,
    help="The service class of your measurement.",
)
@click.option(
    "-i",
    "--interactive-mode",
    is_flag=True,
    help="Utilize interactive input for Python measurement client creation.",
)
def create_client(
    package_name: str, measurement_service_class: Optional[str], interactive_mode: bool
) -> None:
    """Generates a Python measurement client for a measurement service.

    You can use the generated module to interact with the corresponding measurement service.

    PACKAGE_NAME: Name for the Python measurement client package.

    Raises:
        Exception: If the package name is empty or if it misses any configuration or output type.
    """
    discovery_client = DiscoveryClient()
    available_measurement_services = discovery_client.enumerate_services(
        _V2_MEASUREMENT_SERVICE_INTERFACE
    )

    if not available_measurement_services:
        print("Could find any active measurements. Please start one and try again.")
        return

    if interactive_mode:
        package_name, measurement_service_class = _get_user_inputs(available_measurement_services)

    if package_name == "" or not measurement_service_class:
        raise Exception("Package name and/or measurement service class cannot be empty.")

    selected_service = next(
        meas_service
        for meas_service in available_measurement_services
        if meas_service.service_class == measurement_service_class
    )
    measure_docstring = selected_service.annotations["ni/service.description"]

    stub = _get_measurement_stub(discovery_client, measurement_service_class)
    metadata = stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    configuration_metadata_by_id, default_values = _deserialize_configuration_parameters(metadata)
    output_metadata_by_id = _deserialize_output_parameters(metadata)

    measure_parameters_with_type, measure_param_names, enums_by_class = _get_measure_parameters_with_type(configuration_metadata_by_id, default_values)
    measure_return_values_with_type = _get_measure_return_fields_with_type(output_metadata_by_id, enums_by_class)

    _update_enum_default_values(configuration_metadata_by_id, output_metadata_by_id, enums_by_class)

    directory_out_path = pathlib.Path.cwd() / package_name
    directory_out_path.mkdir(exist_ok=True, parents=True)

    _create_file(
        "measurement_client.py.mako",
        f"{package_name}.py",
        directory_out_path,
        measure_docstring=measure_docstring,
        configuration_metadata=configuration_metadata_by_id,
        output_metadata=output_metadata_by_id,
        service_class=measurement_service_class,
        measure_parameters_with_type=measure_parameters_with_type,
        measure_parameters=measure_param_names,
        enum_by_class_name=enums_by_class,
        measure_return_values_with_type=measure_return_values_with_type,
    )

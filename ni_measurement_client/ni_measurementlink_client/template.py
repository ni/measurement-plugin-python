"""Python measurement client template generator."""

import json
import keyword
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
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.discovery import DiscoveryClient, ServiceDescriptor
from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2

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
    Field.TYPE_MESSAGE: int,
}
_INVALID_CHARS = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \n"
_XY_DATA_IMPORT = "from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2"
_IMPORT_MODULES = {}


def add_to_import_modules(key, value):
    global _IMPORT_MODULES
    _IMPORT_MODULES[key] = value


def _check_if_measurement_service_running(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> List[str]:
    try:
        if len(service_class) != 0:
            for service in service_class:
                DiscoveryClient().resolve_service(_V2_MEASUREMENT_SERVICE_INTERFACE, service)
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

def _get_service_descriptors_using_services(
    available_measurement_services: Sequence[ServiceDescriptor],
    service_class: List[str]
) -> Sequence[ServiceDescriptor]:
    preferred_services = []
    for service in available_measurement_services:
        if service.service_class in service_class:
            preferred_services.append(service)

    if len(preferred_services) == 0:
        raise Exception(f"Measurement client creation failed because either all of the entered services: {service_class} are invalid or not running")
    return preferred_services



def _get_module_name_and_service_class_latest(
    available_measurement_services: Sequence[ServiceDescriptor],
) -> Sequence[ServiceDescriptor]:
    print("List of registered measurements: ")
    for i, service in enumerate(available_measurement_services):
        print(f"{i+1}. {service.display_name}")

    user_input = input("Enter 'all' to create client measurements for all active services, or enter a list of serial numbers (separated by spaces) for the desired measurement service client creation: ")

    preferred_services = []

    if user_input.lower() == "all":
        for service in available_measurement_services:
            preferred_services.append(service)
        return preferred_services
    
    unique_inputs = set()
    duplicate_values = []
    inappropriate_values = []
    
    # Split the input string into individual elements by spaces
    elements = user_input.split()
    
    for element in elements:
        try:
            value = int(element)
            if value not in unique_inputs:
                preferred_services.append(available_measurement_services[value - 1])
                unique_inputs.add(value)
            else:
                duplicate_values.append(value)
        except ValueError:
            inappropriate_values.append(element)
    
    if duplicate_values or inappropriate_values:
        log_message = "The following duplicate value(s): {} & the following inappropriate value(s): {} are ignored".format(
            ", ".join(map(str, duplicate_values)) if duplicate_values else "None",
            ", ".join(inappropriate_values) if inappropriate_values else "None"
        )
        print(log_message)

    return preferred_services
    

def _get_module_name_and_service_class(
    available_measurement_services: Sequence[ServiceDescriptor],
) -> Tuple[str, str]:
    print("List of registered measurements: ")
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
    module_name = available_measurement_services[index - 1].service_class
    # module_name = input("Enter the name for the Python measurement client module: ")
    return (module_name, measurement_service_class)


def _get_configuration_metadata_by_id(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    configuration_metadata_by_id = {}
    for configuration in metadata.measurement_signature.configuration_parameters:
        # Only the enum parameters make use of this default value.
        default_value = [0] if configuration.repeated else 0
        configuration_metadata_by_id[configuration.field_number] = ParameterMetadata(
            configuration.name,
            configuration.type,
            configuration.repeated,
            default_value,
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
        raise Exception(f"The following datatypes are not supported:\n1. XY Data\n2. XY Data 1D array")
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
            param_type = f"List[{enum_type_name}]" if metadata.repeated else enum_type_name
            if metadata.repeated:
                values = []
                for val in default_value:
                    enum_value = next(k for k, v in enum_values.items() if v == val)
                    values.append(f"{enum_type_name}.{enum_value}")
                concatenated_default_value = ", ".join(values)
                concatenated_default_value = f"[{concatenated_default_value}]"
                method_params_with_type_and_value.append(
                    f"{parameter_name}: {param_type} = {concatenated_default_value}"
                )
            else:
                enum_value = next(k for k, v in enum_values.items() if v == default_value)
                method_params_with_type_and_value.append(
                    f"{parameter_name}: {param_type} = {enum_type_name}.{enum_value}"
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
                    break

            if metadata.repeated:
                param_type = f"List[{param_type}]"

        if metadata.message_type == "ni.protobuf.types.DoubleXYData":
            param_type = "xydata_pb2.DoubleXYData"
            add_to_import_modules("DoubleXYData", _XY_DATA_IMPORT)

            if metadata.repeated:
                param_type = f"List[{param_type}]"

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
    multiple = True
)
@click.option(
    "-i",
    "--interactive-mode",
    is_flag=True,
    help="Utilize interactive input for Python measurement client creation.",
)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Python measurement client creation for all active services",
)
def create_client(
    module_name: str, measurement_service_class: Optional[List[str]], interactive_mode: bool, all: bool,
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
    
    if all:
        preferred_services = available_measurement_services
    elif interactive_mode:
        preferred_services = _get_module_name_and_service_class_latest(available_measurement_services)
    elif not measurement_service_class:
        raise Exception("Invalid input. Please try again with a valid measurement service class.")
    else:
        preferred_services = _get_service_descriptors_using_services(available_measurement_services,measurement_service_class)

    for service in preferred_services:
        module_name = service.service_class
        measurement_service_class = service.service_class

        
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
            import_modules = _IMPORT_MODULES,
        )

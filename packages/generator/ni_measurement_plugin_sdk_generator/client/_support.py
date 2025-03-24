"""Support functions for the Measurement Plug-In Client generator."""

from __future__ import annotations

import json
import keyword
import pathlib
import re
from collections.abc import Iterable
from enum import Enum
from typing import AbstractSet, TypeVar

import click
import grpc
from google.protobuf import descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.grpc_servicer import (
    frame_metadata_dict,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    ParameterMetadata,
    create_file_descriptor,
    deserialize_parameters,
)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

_INVALID_CHARS = "`~!@#$%^&*()-+={}[]\\|:;',<>.?/ \n"

_XY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import DoubleXYData"
_DOUBLE2DARRAY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.array_pb2 import Double2DArray"
_STRING2DARRAY_DATA_IMPORT = "from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.array_pb2 import String2DArray"
_PATH_IMPORT = "import pathlib"

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
    Field.TYPE_MESSAGE: str,
}

_T = TypeVar("_T")

# List of regex patterns to convert camel case to snake case
_CAMEL_TO_SNAKE_CASE_REGEXES = [
    re.compile("([^_\n])([A-Z][a-z]+)"),
    re.compile("([a-z])([A-Z])"),
    re.compile("([0-9])([^_0-9])"),
    re.compile("([^_0-9])([0-9])"),
]


def get_measurement_service_stub_and_version(
    discovery_client: DiscoveryClient,
    channel_pool: GrpcChannelPool,
    service_class: str,
) -> tuple[v2_measurement_service_pb2_grpc.MeasurementServiceStub, str]:
    """Returns the measurement service stub and version of the given service class."""
    try:
        service_location, service_info = discovery_client.resolve_service_with_information(
            _V2_MEASUREMENT_SERVICE_INTERFACE, service_class
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise click.ClickException(
                f"Could not find any registered measurement with the service class: '{service_class}'."
            )
        elif e.code() == grpc.StatusCode.UNIMPLEMENTED:
            raise click.ClickException(
                "The Measurement Plug-In Client generator requires InstrumentStudio Professional version 2024 Q4 or higher."
            )
        else:
            raise
    channel = channel_pool.get_channel(service_location.insecure_address)

    if not service_info.versions:
        raise click.ClickException(
            "The Measurement Plug-In Client generator requires InstrumentStudio Professional version 2024 Q4 or higher."
        )

    return (
        v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel),
        service_info.versions[0],
    )


def get_all_registered_measurement_info(
    discovery_client: DiscoveryClient,
) -> tuple[list[str], list[str]]:
    """Returns the service classes and display names of all the registered measurement services."""
    registered_measurement_services = discovery_client.enumerate_services(
        _V2_MEASUREMENT_SERVICE_INTERFACE
    )
    measurement_service_classes = [
        measurement_service.service_class for measurement_service in registered_measurement_services
    ]
    measurement_display_names = [
        measurement_service.display_name for measurement_service in registered_measurement_services
    ]
    return measurement_service_classes, measurement_display_names


def get_configuration_and_output_metadata_by_index(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    service_class: str,
    enum_values_by_type: dict[type[Enum], dict[str, int]] = {},
) -> tuple[dict[int, ParameterMetadata], dict[int, ParameterMetadata]]:
    """Returns the configuration and output metadata of the measurement."""
    configuration_parameter_list = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        if configuration.message_type:
            raise click.ClickException(
                f"Measurement configurations do not support message data types ({configuration.message_type} is unsupported)."
            )

        annotations_dict = dict(configuration.annotations.items())
        if _is_enum_param(configuration.type):
            annotations_dict["ni/enum.values"] = _validate_and_transform_enum_annotations(
                configuration.annotations["ni/enum.values"]
            )
        configuration_parameter_list.append(
            ParameterMetadata.initialize(
                display_name=configuration.name,
                type=configuration.type,
                repeated=configuration.repeated,
                default_value=None,
                annotations=annotations_dict,
                message_type=configuration.message_type,
                enum_type=(
                    _get_enum_type(
                        configuration.name, annotations_dict["ni/enum.values"], enum_values_by_type
                    )
                    if _is_enum_param(configuration.type)
                    else None
                ),
            )
        )

    output_parameter_list = []
    for output in metadata.measurement_signature.outputs:
        if output.message_type and output.message_type not in [
            "ni.protobuf.types.DoubleXYData",
            "ni.protobuf.types.Double2DArray",
            "ni.protobuf.types.String2DArray",
        ]:
            raise click.ClickException(
                f"Measurement outputs do not support {output.message_type}. DoubleXYData, Double2DArray and String2DArray message types are supported."
            )

        annotations_dict = dict(output.annotations.items())
        if _is_enum_param(output.type):
            annotations_dict["ni/enum.values"] = _validate_and_transform_enum_annotations(
                output.annotations["ni/enum.values"]
            )
        output_parameter_list.append(
            ParameterMetadata.initialize(
                display_name=output.name,
                type=output.type,
                repeated=output.repeated,
                default_value=None,
                annotations=annotations_dict,
                message_type=output.message_type,
                enum_type=(
                    _get_enum_type(
                        output.name, annotations_dict["ni/enum.values"], enum_values_by_type
                    )
                    if _is_enum_param(output.type)
                    else None
                ),
            )
        )

    create_file_descriptor(
        input_metadata=configuration_parameter_list,
        output_metadata=output_parameter_list,
        service_name=service_class,
        pool=descriptor_pool.Default(),
    )
    configuration_metadata = frame_metadata_dict(configuration_parameter_list)
    output_metadata = frame_metadata_dict(output_parameter_list)

    # Disable path conversion to avoid normalizing path separators and eliminate the need to
    # convert Path objects to strings.
    default_values = deserialize_parameters(
        configuration_metadata,
        metadata.measurement_signature.configuration_defaults.value,
        f"{service_class}.Configurations",
        convert_paths=False,
    )

    for id, default_value in enumerate(default_values, start=1):
        if isinstance(default_value, Enum):
            default_value = default_value.value
        elif isinstance(default_value, list) and any(isinstance(e, Enum) for e in default_value):
            default_value = [e.value for e in default_value]
        configuration_metadata[id] = configuration_metadata[id]._replace(
            default_value=default_value
        )

    return configuration_metadata, output_metadata


def get_configuration_parameters_with_type_and_default_values(
    configuration_metadata: dict[int, ParameterMetadata],
    built_in_import_modules: list[str],
    enum_values_by_type: dict[type[Enum], dict[str, int]] = {},
) -> tuple[str, str]:
    """Returns configuration parameters of the measurement with type and default values."""
    configuration_parameters = []
    parameter_names = []

    for metadata in configuration_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_names.append(parameter_name)

        default_value = metadata.default_value
        parameter_type = _get_configuration_python_type_as_str(metadata.type, metadata.repeated)
        if isinstance(default_value, str):
            default_value = repr(default_value)

        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            parameter_type = "pathlib.PurePath"
            built_in_import_modules.append(_PATH_IMPORT)
            if metadata.repeated:
                formatted_value = ", ".join(
                    f"pathlib.PurePath({repr(value)})" for value in default_value
                )
                default_value = f"[{formatted_value}]"
                parameter_type = f"typing.Iterable[{parameter_type}]"
            else:
                default_value = f"pathlib.PurePath({default_value})"

        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "enum":
            enum_type = _get_enum_type(
                metadata.display_name, metadata.annotations["ni/enum.values"], enum_values_by_type
            )
            parameter_type = enum_type.__name__
            if metadata.repeated:
                values = []
                for val in default_value:
                    enum_value = next((e.name for e in enum_type if e.value == val), None)
                    values.append(f"{parameter_type}.{enum_value}")
                concatenated_default_value = ", ".join(values)
                concatenated_default_value = f"[{concatenated_default_value}]"

                parameter_type = f"typing.Iterable[{parameter_type}]"
                default_value = concatenated_default_value
            else:
                enum_value = next((e.name for e in enum_type if e.value == default_value), None)
                default_value = f"{parameter_type}.{enum_value}"

        configuration_parameters.append(f"{parameter_name}: {parameter_type} = {default_value}")

    configuration_parameters_with_type_and_value = f", ".join(configuration_parameters)
    parameter_names_as_str = ", ".join(parameter_names)

    return (configuration_parameters_with_type_and_value, parameter_names_as_str)


def get_output_parameters_with_type(
    output_metadata: dict[int, ParameterMetadata],
    built_in_import_modules: list[str],
    custom_import_modules: list[str],
    enum_values_by_type: dict[type[Enum], dict[str, int]] = {},
) -> list[str]:
    """Returns the output parameters of the measurement with type."""
    output_parameters_with_type: list[str] = []
    for metadata in output_metadata.values():
        parameter_name = _get_python_identifier(metadata.display_name)
        parameter_type = _get_output_python_type_as_str(metadata.type, metadata.repeated)

        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            parameter_type = "pathlib.Path"
            built_in_import_modules.append(_PATH_IMPORT)

            if metadata.repeated:
                parameter_type = f"typing.Sequence[{parameter_type}]"

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            parameter_type = "DoubleXYData"
            custom_import_modules.append(_XY_DATA_IMPORT)

            if metadata.repeated:
                parameter_type = f"typing.Sequence[{parameter_type}]"

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.Double2DArray":
            parameter_type = "Double2DArray"
            custom_import_modules.append(_DOUBLE2DARRAY_DATA_IMPORT)

            if metadata.repeated:
                raise click.ClickException(
                    f"Repeated Double 2D Array are not supported for output parameter "
                    f"'{parameter_name}'. Please contact the measurement developer."
                )

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.String2DArray":
            parameter_type = "String2DArray"
            custom_import_modules.append(_STRING2DARRAY_DATA_IMPORT)

            if metadata.repeated:
                raise click.ClickException(
                    f"Repeated String 2D Array are not supported for output parameter "
                    f"'{parameter_name}'. Please contact the measurement developer."
                )

        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "enum":
            enum_type_name = _get_enum_type(
                metadata.display_name, metadata.annotations["ni/enum.values"], enum_values_by_type
            ).__name__
            parameter_type = (
                f"typing.Sequence[{enum_type_name}]" if metadata.repeated else enum_type_name
            )

        output_parameters_with_type.append(f"{parameter_name}: {parameter_type}")

    return output_parameters_with_type


def to_ordered_set(values: Iterable[_T]) -> AbstractSet[_T]:
    """Converts an iterable to an ordered set."""
    return dict.fromkeys(values).keys()


def resolve_output_directory(directory_out: str | None = None) -> pathlib.Path:
    """Returns the validated directory output path."""
    if directory_out is None:
        directory_out_path = pathlib.Path.cwd()
    else:
        directory_out_path = pathlib.Path(directory_out)

    if not directory_out_path.exists():
        raise click.ClickException(f"The specified directory '{directory_out}' was not found.")

    return directory_out_path


def validate_identifier(name: str, name_type: str) -> None:
    """Validates whether the given string is a valid Python identifier."""
    if not _is_python_identifier(name):
        raise click.ClickException(
            f"The {name_type} name '{name}' is not a valid Python identifier."
        )


def extract_base_service_class(service_class: str) -> str:
    """Creates a base service class from the measurement service class."""
    base_service_class = service_class.split(".")[-1]
    base_service_class = _remove_suffix(base_service_class)

    if not base_service_class.isidentifier():
        raise click.ClickException(
            f"Client creation failed for '{service_class}'.\nEither provide a module name or update the measurement with a valid service class."
        )
    if not any(ch.isupper() for ch in base_service_class):
        print(
            f"Warning: The service class '{service_class}' does not adhere to the recommended format."
        )
    return base_service_class


def create_module_name(base_service_class: str, generated_modules: list[str]) -> str:
    """Creates a unique module name using the base service class."""
    base_module_name = _camel_to_snake_case(base_service_class) + "_client"
    module_name = base_module_name
    counter = 2

    while module_name in generated_modules:
        module_name = f"{base_module_name}{counter}"
        counter += 1

    return module_name


def create_class_name(base_service_class: str) -> str:
    """Creates a class name using base service class."""
    return base_service_class.replace("_", "") + "Client"


def get_selected_measurement_service_class(
    selection: int, measurement_service_classes: list[str]
) -> str:
    """Returns the selected measurement service class."""
    if not (1 <= selection <= len(measurement_service_classes)):
        raise click.ClickException(
            f"Input {selection} is not invalid. Please try again by selecting a valid measurement from the list."
        )
    return measurement_service_classes[selection - 1]


def validate_measurement_service_classes(measurement_service_classes: list[str]) -> None:
    """Validates whether the given measurement service classes list is empty."""
    if len(measurement_service_classes) == 0:
        raise click.ClickException("No registered measurements.")


def _get_python_identifier(input_string: str) -> str:
    valid_identifier = input_string.lower()
    if not valid_identifier.isidentifier():
        for invalid_char in _INVALID_CHARS:
            valid_identifier = valid_identifier.replace(invalid_char, "_")

    if valid_identifier[0].isdigit() or keyword.iskeyword(valid_identifier):
        valid_identifier = f"_{valid_identifier}"
    return valid_identifier


def _get_configuration_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    python_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)

    if python_type is None:
        raise TypeError(f"Invalid data type: '{type}'.")

    if is_array:
        return f"typing.Iterable[{python_type.__name__}]"
    return python_type.__name__


def _get_output_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    python_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)

    if python_type is None:
        raise TypeError(f"Invalid data type: '{type}'.")

    if is_array:
        return f"typing.Sequence[{python_type.__name__}]"
    return python_type.__name__


def _camel_to_snake_case(camel_case_string: str) -> str:
    partial = camel_case_string
    for regex in _CAMEL_TO_SNAKE_CASE_REGEXES:
        partial = regex.sub(r"\1_\2", partial)

    return partial.lower()


def _remove_suffix(string: str) -> str:
    suffixes = ["_Python", "_LabVIEW", "_NET"]
    for suffix in suffixes:
        if string.endswith(suffix):
            return string.removesuffix(suffix)
    return string


def _is_python_identifier(input_string: str | None) -> bool:
    if input_string is None:
        return False
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return re.fullmatch(pattern, input_string) is not None


def _is_enum_param(parameter_type: int) -> bool:
    return parameter_type == FieldDescriptorProto.TYPE_ENUM


def _get_enum_type(
    parameter_name: str,
    enum_annotations: str,
    enum_values_by_type: dict[type[Enum], dict[str, int]],
) -> type[Enum]:
    enum_values = dict(json.loads(enum_annotations))
    for existing_enum_type, existing_enum_values in enum_values_by_type.items():
        if existing_enum_values == enum_values:
            return existing_enum_type

    new_enum_type_name = _get_enum_class_name(parameter_name)
    # MyPy error: Enum() expects a string literal as the first argument.
    # Ignoring this error because MyPy cannot validate dynamic Enum creation statically.
    new_enum_type = Enum(new_enum_type_name, enum_values)  # type: ignore[misc]
    enum_values_by_type[new_enum_type] = enum_values
    return new_enum_type


def _get_enum_class_name(name: str) -> str:
    name = re.sub(r"[^\w\s]", "", name).replace("_", " ")
    split_string = name.split()
    if len(split_string) > 1:
        name = "".join(s.capitalize() for s in split_string)
    else:
        name = name[0].upper() + name[1:]
    return f"{name}Enum"


def _validate_and_transform_enum_annotations(enum_annotations: str) -> str:
    enum_values = dict(json.loads(enum_annotations))
    transformed_enum_annotations = {}
    for enum_value, value in enum_values.items():
        original_enum_value = enum_value

        enum_value = re.sub(r"\W+", "_", enum_value)
        if enum_value[0].isdigit():
            enum_value = f"k_{enum_value}"

        # Check for enum values that are only special characters.
        if not enum_value.strip("_"):
            raise click.ClickException(f"The enum value '{original_enum_value}' is invalid.")

        transformed_enum_annotations[enum_value] = value

    return json.dumps(transformed_enum_annotations)

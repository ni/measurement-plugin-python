from enum import Enum
import json
import keyword
from typing import Any, Dict, List, Tuple

import click
import grpc
from google.protobuf.type_pb2 import Field
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.parameter import decoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import create_file_descriptor


_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
_XY_DATA_IMPORT = "from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2"
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
_IMPORT_MODULES = {}

def _check_if_measurement_service_running(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> str:
    try:
        if service_class:
            DiscoveryClient().resolve_service(_V2_MEASUREMENT_SERVICE_INTERFACE, service_class)            
        return service_class
    except Exception:
        raise click.BadParameter(
            f"Could not find any registered measurement with service class: '{service_class}'."
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

def _get_configuration_parameter_list(
        metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    configuration_parameter_list = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        enum_type = Enum if int(configuration.type) == 14 else None
        configuration_parameter_list.append(
            ParameterMetadata.initialize(
                True,
                configuration.name,
                configuration.type,
                configuration.repeated,
                None,
                configuration.annotations,
                configuration.message_type,
                enum_type
            )
        )

    return configuration_parameter_list

def _get_output_parameter_list(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    output_parameter_list = []
    for output in metadata.measurement_signature.outputs:
        enum_type = Enum if int(output.type) == 14 else None
        output_parameter_list.append(
                ParameterMetadata.initialize(
                False,
                output.name,
                output.type,
                output.repeated,
                None,
                output.annotations,
                output.message_type,
                enum_type
            )
        )

    return output_parameter_list

def _frame_metadata_dict(
    parameter_list: List[ParameterMetadata],
) -> Dict[int, ParameterMetadata]:
    metadata_dict = {}
    for i, parameter in enumerate(parameter_list, start=1):
        metadata_dict[i] = parameter

    return metadata_dict

def _get_configuration_metadata(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    service_class : str
) -> Dict[int, ParameterMetadata]:    
    configuration_parameter_list = _get_configuration_parameter_list(metadata)
    output_parameter_list = _get_output_parameter_list(metadata)
    configuration_metadata = _frame_metadata_dict(configuration_parameter_list)

    create_file_descriptor(
            service_name=service_class,
            output_metadata=output_parameter_list,
            input_metadata=configuration_parameter_list,
            pool=descriptor_pool.Default(),
        )

    params = decoder.deserialize_parameters(
        configuration_metadata, metadata.measurement_signature.configuration_defaults.value, service_class + ".Configurations"
    )

    default_values = [None] * params.__len__()
    for k, v in params.items():
        configuration_metadata[k] = configuration_metadata[k]._replace(default_value=v)
        default_values[k - 1] = v

    return configuration_metadata

def _get_output_metadata(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    output_parameter_list = _get_output_parameter_list(metadata)
    output_metadata = _frame_metadata_dict(output_parameter_list)
    return output_metadata

def _remove_invalid_characters(name: str, new_char: str) -> str:
    # Replace any spaces or special characters with an '_'.
    if not name.isidentifier():
        for invalid_char in _INVALID_CHARS:
            name = name.replace(invalid_char, new_char)

    # Python identifiers cannot begin with an integer. So prefix '_' if it does.
    if name[0].isdigit() or keyword.iskeyword(name):
        name = "_" + name
    
    return name

def _get_python_module_name(name: str) -> str:
    module_name = class_name = name.replace(" ", "_").lower()
    module_name = _remove_invalid_characters(module_name, "")
    return module_name

def _get_python_identifier(name: str) -> str:
    var_name = name.lower()
    var_name = _remove_invalid_characters(name, "_")
    return var_name

def _get_python_class_name(name: str) -> str:
    class_name = name.replace("_", " ").title().replace(" ", "")
    class_name = _remove_invalid_characters(class_name, "_")
    return class_name + "Enum"


def _get_python_type_as_str(type: Field.Kind.ValueType, is_array: bool) -> str:
    py_type = _PROTO_DATATYPE_TO_PYTYPE_LOOKUP.get(type)
    if py_type is None:
        raise Exception(f"The following datatypes are not supported:\n1. XY Data\n2. XY Data 1D array")
    
    if is_array:
        return f"List[{py_type.__name__}]"
    return py_type.__name__


def _get_enum_values(parameter_metadata: ParameterMetadata) -> Dict[str, Any]:
    enum_values_in_json = parameter_metadata.annotations["ni/enum.values"]
    enum_values: Dict[str, Any] = json.loads(enum_values_in_json)

    # Replace any spaces or special characters with an '_'.
    serialized_enum_values : Dict[str, Any] = {}
    for k, v in enum_values.items():
        k = _remove_invalid_characters(k, "_")
        serialized_enum_values[k] = v

    return serialized_enum_values


def _get_measure_parameters_with_type_and_default_value(
    configuration_metadata: Dict[int, ParameterMetadata]
) -> Tuple[str, str, Dict[str, Dict[str, Any]]]:
    method_params_with_type_and_value = []
    parameter_names = []
    enum_values_by_name: Dict[str, Dict[str, Any]] = dict()

    for metadata in configuration_metadata.values():
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
                enum_value = next(k for k, v in enum_values.items() if v == default_value.value)
                method_params_with_type_and_value.append(
                    f"{parameter_name}: {param_type} = {enum_type_name}.{enum_value}"
                )
        else:
            method_params_with_type_and_value.append(f"{parameter_name}: {param_type} = {default_value}")

    # Use newline and spaces to align the method parameters appropriately in the generated file.
    method_parameters_with_type_and_value = ",\n        ".join(method_params_with_type_and_value)
    parameter_names_as_str = ", ".join(parameter_names)

    return (method_parameters_with_type_and_value, parameter_names_as_str, enum_values_by_name)


def _get_measure_output_fields_with_type(
    output_metadata: Dict[int, ParameterMetadata],
    enum_values_by_type_name: Dict[str, Dict[str, Any]],
) -> str:
    output_names_with_type = []
    for metadata in output_metadata.values():
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

        if metadata.message_type and metadata.message_type == "ni.protobuf.types.DoubleXYData":
            param_name = "xydata_pb2.DoubleXYData"
            _IMPORT_MODULES["DoubleXYData"] = _XY_DATA_IMPORT

            if metadata.repeated:
                param_type = f"List[{param_type}]"

        output_names_with_type.append(f"{param_name}: {param_type}")

    return "\n    ".join(output_names_with_type)
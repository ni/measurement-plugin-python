<%page args="enum_by_class_name, measure_return_values_with_type, output_metadata"/>\
\
% if enum_by_class_name:
from enum import Enum
% endif
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.parameter import encoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
)
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import create_file_descriptor

% for enum_name, enum_value in enum_by_class_name.items():
class ${enum_name}(Enum):
    % for key, val in enum_value.items():
    ${key} = ${val}
    % endfor
% endfor

<% output_type = "None" %>\
% if output_metadata:

class Output(NamedTuple):
    """Measurement result container."""

    ${measure_return_values_with_type}

<% output_type = "Output" %>\
% endif

def _get_configuration_parameter_list(
        metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> List[ParameterMetadata]:
    configuration_parameter_list = []
    for configuration in metadata.measurement_signature.configuration_parameters:
        % if enum_by_class_name:
        enum_type = ${next(iter(enum_by_class_name))}
        % else:
        enum_type = None
        % endif
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
        % if enum_by_class_name:
        enum_type = ${next(iter(enum_by_class_name))}
        % else:
        enum_type = None
        % endif
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

def _create_file_descriptor(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
    service_class : str
) -> None:
    configuration_parameter_list = _get_configuration_parameter_list(metadata)
    output_parameter_list = _get_output_parameter_list(metadata)

    create_file_descriptor(
        service_name=service_class,
        output_metadata=output_parameter_list,
        input_metadata=configuration_parameter_list,
        pool=descriptor_pool.Default(),
    )    
    
def _get_measure_request(
    service_class : str,
    configuration_metadata : Dict[int, ParameterMetadata],
    args: Any
) -> v2_measurement_service_pb2.MeasureRequest:
    serialized_configuration = any_pb2.Any(
        value=encoder.serialize_parameters(configuration_metadata, args, service_class +  ".Configurations")
    )
    return v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=serialized_configuration
    )

% if output_metadata:
def _parse_enum_values(
    output_metadata : Dict[int, ParameterMetadata],
    output_values: Dict[int, Any]
) -> Dict[int, Any]:
    for key, metadata in output_metadata.items():
        if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
            enum_type = type(eval(metadata.default_value))
            if metadata.repeated:
                enum_values = []
                for value in output_values[key]:
                    enum_values.append(enum_type(int(value)))
                output_values[key] = enum_values
            else:
                output_values[key] = enum_type(int(output_values[key]))
    return output_values
% endif
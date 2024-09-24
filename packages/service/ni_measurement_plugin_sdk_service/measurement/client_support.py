"""Support functions for the Measurement Plug-In Client."""

from pathlib import Path
from typing import Any, Dict, Iterable, List
from ni_measurement_plugin_sdk_service._internal.parameter.decoder import deserialize_parameters
from ni_measurement_plugin_sdk_service._internal.parameter.encoder import serialize_parameters
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.parameter.serialization_descriptors import (
    create_file_descriptor,
)

__all__ = [
    "create_file_descriptor",
    "convert_paths_to_strings",
    "convert_strings_to_paths",
    "deserialize_parameters",
    "ParameterMetadata",
    "serialize_parameters",
]


def convert_paths_to_strings(parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_values: Iterable[Any]) -> List[Any]:
    """Convert path parameters from Path objects to strings.
    
    Args:
        parameter_metadata_dict: Parameter metadata by ID.

        parameter_values: The parameter values.

    Returns:
        The parameter values with Path objects converted to strings, where appropriate.
    """
    result: List[Any] = []

    for index, parameter_value in enumerate(parameter_values):
        metadata = parameter_metadata_dict[index + 1]
        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            if metadata.repeated:
                result.append([_path_to_string(value) for value in parameter_value])
            else:
                result.append(_path_to_string(parameter_value))
        else:
            result.append(parameter_value)

    return result


def convert_strings_to_paths(parameter_metadata_dict: Dict[int, ParameterMetadata], parameter_values: Iterable[Any]) -> List[Any]:
    """Convert path parameters from strings to Path objects.
    
    Args:
        parameter_metadata_dict: Parameter metadata by ID.

        parameter_values: The parameter values.

    Returns:
        The parameter values with strings converted to Path objects, where approriate.
    """
    result: List[Any] = []

    for index, parameter_value in enumerate(parameter_values):
        metadata = parameter_metadata_dict[index + 1]
        if metadata.annotations and metadata.annotations.get("ni/type_specialization") == "path":
            if metadata.repeated:
                result.append([_string_to_path(value) for value in parameter_value])
            else:
                result.append(_string_to_path(parameter_value))
        else:
            result.append(parameter_value)

    return result


def _path_to_string(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    else:
        return value
    

def _string_to_path(value: Any) -> Any:
    if isinstance(value, str):
        return Path(value)
    else:
        return value
"""Contains classes that represents metadata."""
import json
from enum import Enum
from typing import Any, Dict, NamedTuple, Tuple

from google.protobuf import type_pb2

from ni_measurementlink_service._internal.parameter.serialization_strategy import (
    Context,
)
from ni_measurementlink_service.measurement.info import TypeSpecialization


class ParameterMetadata(NamedTuple):
    """Class that represents the metadata of parameters.

    Attributes
    ----------
        display_name (str): The display name of the parameter.

        type (type_pb2.Field): The datatype of the parameter
        represented by the gRPC Field Enum.

        repeated (bool): Represent if the parameter is a scalar or 1D array.

        True for 1DArray and false for scalar.

        default_value (Any): The default value of the parameter.

        annotations (Dict[str,str]): Represents a set of annotations on the type.

    """

    display_name: str
    type: type_pb2.Field.Kind.ValueType
    repeated: bool
    default_value: Any
    annotations: Dict[str, str]


def validate_default_value_type(parameter_metadata: ParameterMetadata) -> None:
    """Validate and raise exception if the default value does not match the type info.

    Args
    ----
        parameter_metadata (ParameterMetadata): Parameter metadata

    Raises
    ------
        TypeError: If default value does not match the Datatype.

    """
    display_name = parameter_metadata.display_name
    default_value = parameter_metadata.default_value
    if default_value is None:
        return None

    expected_type = type(
        Context.get_type_default(parameter_metadata.type, parameter_metadata.repeated)
    )
    has_enum_values_annotation, enum_values_annotation = try_get_enum_values_annotation(
        parameter_metadata
    )

    if parameter_metadata.repeated:
        if not isinstance(default_value, expected_type):
            raise TypeError(
                f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
            )
        expected_element_type = type(Context.get_type_default(parameter_metadata.type, False))
        if has_enum_values_annotation:
            for element in default_value:
                if not _is_default_enum_match_annotations(element, enum_values_annotation):
                    raise TypeError(
                        f"The default value, `{element}`, for '{display_name}' is not valid. Expected values: `{enum_values_annotation}`."
                    )
        else:
            for element in default_value:
                if not isinstance(element, expected_element_type):
                    raise TypeError(
                        f"Unexpected element of type {type(element)} in the default value for '{display_name}'. Expected element type: {expected_element_type}."
                    )
    else:
        if has_enum_values_annotation:
            if not _is_default_enum_match_annotations(default_value, enum_values_annotation):
                raise TypeError(
                    f"The default value, `{default_value}`, for '{display_name}' is not valid. Expected values: `{enum_values_annotation}`."
                )
        else:
            if not isinstance(default_value, expected_type):
                raise TypeError(
                    f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
                )
    return None


def try_get_enum_values_annotation(parameter_metadata: ParameterMetadata) -> Tuple[bool, str]:
    """Gets the value for the "ni/enum.values" annotation if it exists.

    Args
    ----
        parameter_metadata (ParameterMetadata): Parameter metadata

    Returns
    -------
        Tuple[bool, str]: A Tuple that contains both the value of
        the "ni/enum.values" annotation and whether we were successful
        in obtaining it.

    """
    if (
        "ni/type_specialization" in parameter_metadata.annotations
        and parameter_metadata.annotations["ni/type_specialization"]
        == TypeSpecialization.Enum.value
        and "ni/enum.values" in parameter_metadata.annotations
    ):
        enum_values = parameter_metadata.annotations["ni/enum.values"]
        if enum_values != "" and enum_values is not None:
            return True, enum_values
    return False, ""


def _is_default_enum_match_annotations(default_value: Any, enum_values_annotation: str):
    if not isinstance(default_value, Enum):
        return False
    user_enum = json.loads(enum_values_annotation.replace("'", '"'))
    if (any(member == default_value.name for member in user_enum)
        and user_enum[default_value.name] == default_value.value):
        return True
    return False

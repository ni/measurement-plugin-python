"""Contains classes that represents metadata."""

import json
from enum import Enum
from typing import Any, Dict, Iterable, NamedTuple

from google.protobuf import type_pb2

from ni_measurementlink_service._annotations import (
    ENUM_VALUES_KEY,
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurementlink_service._internal.parameter import serialization_strategy
from ni_measurementlink_service.measurement.info import TypeSpecialization


class ParameterMetadata(NamedTuple):
    """Class that represents the metadata of parameters."""

    display_name: str
    """The display name of the parameter."""

    type: type_pb2.Field.Kind.ValueType
    """The datatype of the parameter represented by the gRPC field enum."""

    repeated: bool
    """Indicates whether the parameter is a scalar or 1D array.
    
    True for 1D array and false for scalar."""

    default_value: Any
    """The default value of the parameter."""

    annotations: Dict[str, str]
    """Represents a set of annotations on the type."""

    message_type: str = ""
    """The gRPC full name of the message type. 
    
    Required when 'type' is Kind.TypeMessage. Ignored for any other 'type'.
    """


def validate_default_value_type(parameter_metadata: ParameterMetadata) -> None:
    """Validate and raise exception if the default value does not match the type info.

    Args:
        parameter_metadata (ParameterMetadata): Parameter metadata

    Raises:
        TypeError: If default value does not match the Datatype.
    """
    default_value = parameter_metadata.default_value
    if default_value is None:
        return None

    expected_type = type(
        serialization_strategy.get_type_default(
            parameter_metadata.type, parameter_metadata.repeated
        )
    )
    display_name = parameter_metadata.display_name
    enum_values_annotation = get_enum_values_annotation(parameter_metadata)

    if parameter_metadata.repeated:
        expected_element_type = type(
            serialization_strategy.get_type_default(parameter_metadata.type, False)
        )
        _validate_default_value_type_for_repeated_type(
            default_value,
            expected_type,
            expected_element_type,
            enum_values_annotation,
            display_name,
        )
    else:
        _validate_default_value_type_for_scalar_type(
            default_value, expected_type, enum_values_annotation, display_name
        )
    return None


def _validate_default_value_type_for_scalar_type(
    default_value: object, expected_type: type, enum_values_annotation: str, display_name: str
) -> None:
    """Validate and raise exception if the default value does not match the type info."""
    if enum_values_annotation:
        user_enum_dict = json.loads(enum_values_annotation)
        _validate_default_value_type_for_enum_type(
            default_value, user_enum_dict, enum_values_annotation, display_name
        )
    else:
        _validate_default_value_type_for_basic_type(default_value, expected_type, display_name)


def _validate_default_value_type_for_repeated_type(
    default_value: Iterable[object],
    expected_type: type,
    expected_element_type: type,
    enum_values_annotation: str,
    display_name: str,
) -> None:
    """Validate and raise exception if the default value does not match the type info."""
    if not isinstance(default_value, expected_type):
        raise TypeError(
            f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
        )

    if enum_values_annotation:
        user_enum_dict = json.loads(enum_values_annotation)
        for element in default_value:
            _validate_default_value_type_for_enum_type(
                element, user_enum_dict, enum_values_annotation, display_name
            )
    else:
        for element in default_value:
            _validate_default_value_type_for_basic_type(
                element, expected_element_type, display_name
            )


def _validate_default_value_type_for_basic_type(
    default_value: object,
    expected_type: type,
    display_name: str,
) -> None:
    if not isinstance(default_value, expected_type):
        raise TypeError(
            f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
        )


def _validate_default_value_type_for_enum_type(
    default_value: object,
    user_enum: Dict[str, int],
    enum_values_annotation: str,
    display_name: str,
) -> None:
    if not _is_valid_enum_value(default_value, user_enum):
        raise TypeError(
            f"Invalid default value, `{default_value}`, for enum parameter '{display_name}'. Expected values: `{enum_values_annotation}`."
        )


def get_enum_values_annotation(parameter_metadata: ParameterMetadata) -> str:
    """Gets the value for the "ni/enum.values" annotation if it exists.

    Args:
        parameter_metadata (ParameterMetadata): Parameter metadata

    Returns:
        str: The value of "ni/enum.values" annotation
    """
    if parameter_metadata.annotations.get(TYPE_SPECIALIZATION_KEY) == TypeSpecialization.Enum.value:
        return parameter_metadata.annotations.get(ENUM_VALUES_KEY, "")
    else:
        return ""


def _is_valid_enum_value(enum_value: object, user_enum: Dict[str, int]) -> bool:
    if isinstance(enum_value, Enum):
        return enum_value.name in user_enum and user_enum[enum_value.name] == enum_value.value
    elif isinstance(enum_value, int):
        return enum_value in user_enum.values()
    else:
        return False

"""Contains classes that represents metadata."""

from __future__ import annotations

import json
from collections.abc import Iterable
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple, Union

from google.protobuf import type_pb2

from ni_measurement_plugin_sdk_service._annotations import (
    ENUM_VALUES_KEY,
    TYPE_SPECIALIZATION_KEY,
)
from ni_measurement_plugin_sdk_service._internal.parameter._get_type import (
    get_type_default,
)
from ni_measurement_plugin_sdk_service.measurement.info import TypeSpecialization

if TYPE_CHECKING:
    from google.protobuf.internal.enum_type_wrapper import _EnumTypeWrapper

    SupportedEnumType = Union[type[Enum], _EnumTypeWrapper]

_VALID_CHARS = set(" ().,;:!?-_'+")


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

    annotations: dict[str, str]
    """Represents a set of annotations on the type."""

    message_type: str = ""
    """The gRPC full name of the message type. 
    
    Required when 'type' is Kind.TypeMessage. Ignored for any other 'type'.
    """

    field_name: str = ""
    """display_name in snake_case format."""

    enum_type: SupportedEnumType | None = None
    """Enum type of parameter"""

    @staticmethod
    def initialize(
        display_name: str,
        type: type_pb2.Field.Kind.ValueType,
        repeated: bool,
        default_value: Any,
        annotations: dict[str, str],
        message_type: str = "",
        enum_type: SupportedEnumType | None = None,
    ) -> ParameterMetadata:
        """Initialize ParameterMetadata with field_name."""
        _validate_display_name(display_name)
        underscore_display_name = display_name.replace(" ", "_")

        if all(char.isalnum() or char == "_" for char in underscore_display_name):
            field_name = underscore_display_name
        else:
            field_name = "".join(
                char for char in underscore_display_name if char.isalnum() or char == "_"
            )
        parameter_metadata = ParameterMetadata(
            display_name,
            type,
            repeated,
            default_value,
            annotations,
            message_type,
            field_name,
            enum_type,
        )
        _validate_default_value_type(parameter_metadata)
        return parameter_metadata


def _validate_display_name(display_name: str) -> None:
    """Validate and raise exception if 'display_name' has invalid characters.

    Raises:
        ValueError: If display_name has invalid characters.
    """
    if not display_name:
        raise ValueError("The display name cannot be an empty string.")
    elif not display_name[0].isalpha():
        raise ValueError(f"The first character in display name '{display_name}' must be a letter.")
    elif not all(char in _VALID_CHARS or char.isalnum() for char in display_name):
        raise ValueError(f"There are invalid characters in display name '{display_name}'.")


def _validate_default_value_type(parameter_metadata: ParameterMetadata) -> None:
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
        get_type_default(parameter_metadata.type, parameter_metadata.repeated, type(default_value))
    )
    display_name = parameter_metadata.display_name
    enum_values_annotation = get_enum_values_annotation(parameter_metadata)

    if parameter_metadata.repeated:
        if not isinstance(default_value, list):
            raise TypeError(f"The default value '{default_value}' is not a list.")
        if len(default_value) > 0:
            expected_element_type = type(
                get_type_default(parameter_metadata.type, False, type(default_value[0]))
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
        if expected_type is float and isinstance(default_value, int):
            return None
        raise TypeError(
            f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
        )


def _validate_default_value_type_for_enum_type(
    default_value: object,
    user_enum: dict[str, int],
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


def _is_valid_enum_value(enum_value: object, user_enum: dict[str, int]) -> bool:
    if isinstance(enum_value, Enum):
        return enum_value.name in user_enum and user_enum[enum_value.name] == enum_value.value
    elif isinstance(enum_value, int):
        return enum_value in user_enum.values()
    else:
        return False

"""Contains classes that represents metadata."""
from typing import Any, Dict, NamedTuple, Tuple
from enum import Enum
import json

from google.protobuf import type_pb2

from ni_measurementlink_service._internal.parameter.serialization_strategy import Context
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

    if not isinstance(default_value, expected_type):
        has_enum_values_annotation, enum_values_annotation = _try_get_enum_values_annotation(parameter_metadata)
        if has_enum_values_annotation:
            userEnum = json.loads(enum_values_annotation.replace("'", "\""))
            userEnumClass = Enum("UserDefinedEnum", userEnum)
            if ((not any(member.value == default_value.value for member in userEnumClass)) or 
                (not userEnumClass(default_value.value).name == default_value.name)):
                raise TypeError(
                    f"The default value, `{default_value}`, for '{display_name}' is not valid. Expected values: `{userEnum}`."
                )
        else:
            raise TypeError(
                f"Unexpected type {type(default_value)} in the default value for '{display_name}'. Expected type: {expected_type}."
            )

    if parameter_metadata.repeated:
        expected_element_type = type(Context.get_type_default(parameter_metadata.type, False))
        for element in default_value:
            if not isinstance(element, expected_element_type):
                raise TypeError(
                    f"Unexpected element of type {type(element)} in the default value for '{display_name}'. Expected element type: {expected_element_type}."
                )
    return None

def _try_get_enum_values_annotation(parameter_metadata: ParameterMetadata)-> Tuple[bool, str]:
    if ("ni/type_specialization" in parameter_metadata.annotations and 
        parameter_metadata.annotations["ni/type_specialization"] == TypeSpecialization.Enum.value and
        "ni/enum.values" in parameter_metadata.annotations):
        enum_values = parameter_metadata.annotations["ni/enum.values"]
        if enum_values != "" and enum_values is not None:
            return True, enum_values
    return False, ""

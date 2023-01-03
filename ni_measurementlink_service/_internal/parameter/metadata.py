"""Contains classes that represents metadata."""
from typing import Any, Dict, NamedTuple

from google.protobuf import type_pb2

from ni_measurementlink_service._internal.parameter.serialization_strategy import Context


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

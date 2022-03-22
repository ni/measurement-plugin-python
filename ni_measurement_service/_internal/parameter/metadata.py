"""Contains classes that represents metadata."""
from typing import Any, NamedTuple

import google.protobuf.type_pb2 as type_pb2
from ni_measurement_service._internal.parameter.serializationstrategy import Context


class ParameterMetadata(NamedTuple):
    """Class that represents the metadata of parameters.

    Attributes
    ----------
        display_name (str): The display name of the parameter.
        type (google.protobuf.type_pb2.Field): The datatype of the parameter
        represented by the gRPC Field Enum.
        repeated (bool): Represent if the parameter is a scalar or 1D array.
        True for 1DArray and false for scalar.
        default_value (Any): The default value of the parameter.

    """

    display_name: str
    type: type_pb2.Field
    repeated: bool
    default_value: Any


def validate_default_value_type(parameter_metadata: ParameterMetadata) -> None:
    """Validate and raise expection if the default value is not matching the type info.

    Args
    ----
        parameter_metadata (ParameterMetadata): Parameter metadata

    Raises
    ------
        TypeError: If default value is not matching the Datatype.

    """
    display_name = parameter_metadata.display_name
    default_value = parameter_metadata.default_value
    if default_value is None:
        return None

    expected_type = type(
        Context.get_type_default(parameter_metadata.type, parameter_metadata.repeated)
    )

    if type(default_value) != expected_type:
        raise TypeError(
            f"Default value for '{display_name}' cannot be of type: {type(default_value)}.Expected type: {expected_type}."
        )

    if parameter_metadata.repeated:
        expected_element_type = type(Context.get_type_default(parameter_metadata.type, False))
        for element in default_value:
            if type(element) != expected_element_type:
                raise TypeError(
                    f"Default value list for '{display_name}' cannot contain an element of type: {type(element)}.Expected type for all elements: {expected_type}."
                )
    return None

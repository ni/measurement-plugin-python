"""Contains classes that represents metadata."""
from typing import Any, NamedTuple

import google.protobuf.type_pb2 as type_pb2


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

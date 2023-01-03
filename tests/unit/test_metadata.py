"""Contains tests to validate metadata.py."""
import pytest

from ni_measurementlink_service._internal.parameter import metadata
from ni_measurementlink_service.measurement.info import DataType


@pytest.mark.parametrize(
    "type,default_value",
    [
        (DataType.Int32, "string_default_value"),
        (DataType.Int32, 2.0),
        (DataType.Boolean, 1),
        (DataType.Boolean, 0),
        (DataType.String, True),
        (DataType.DoubleArray1D, 0.5),
        (DataType.Double, 1),
    ],
)
def test___default_value_different_from_type___validate___raises_type_exception(
    type, default_value
):
    """Tests if exceptions are raised when the default value provided is not matching the type.

    Args:
    ----
        type (DataType): Type of the parameter.
        default_value (Any): Default value of the parameter.

    """
    grpc_field_type, repeated, type_specialization = type.value
    parameter_metadata = metadata.ParameterMetadata(
        "test_display_name", grpc_field_type, repeated, default_value, annotations={}
    )

    with pytest.raises(TypeError):
        metadata.validate_default_value_type(parameter_metadata)


@pytest.mark.parametrize(
    "type,default_value",
    [
        (DataType.Int32, 1),
        (DataType.Boolean, True),
        (DataType.String, "string_default_value"),
        (DataType.DoubleArray1D, [0.5, 0.1]),
        (DataType.Double, 1.0),
    ],
)
def test___default_value_same_as_type___validate___raises_no_exception(type, default_value):
    """Tests if no exceptions are raised when the default value provided is matching the type.

    Args:
    ----
        type (DataType): Type of the parameter.
        default_value (Any): Default value of the parameter.

    """
    grpc_field_type, repeated, type_specialization = DataType.Int32.value
    parameter_metadata = metadata.ParameterMetadata(
        "test_display_name", grpc_field_type, repeated, 1, annotations={}
    )

    metadata.validate_default_value_type(parameter_metadata)  # implicitly assert does not throw

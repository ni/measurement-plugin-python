"""Contains tests to validate the serializationstrategy.py. """
import pytest
from google.protobuf import type_pb2

from ni_measurement_service._internal.parameter import serialization_strategy


@pytest.mark.parametrize(
    "type,is_repeated,expected_encoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, serialization_strategy.FloatEncoder),
        (type_pb2.Field.TYPE_DOUBLE, False, serialization_strategy.DoubleEncoder),
        (type_pb2.Field.TYPE_INT32, False, serialization_strategy.IntEncoder),
        (type_pb2.Field.TYPE_INT64, False, serialization_strategy.IntEncoder),
        (type_pb2.Field.TYPE_UINT32, False, serialization_strategy.UIntEncoder),
        (type_pb2.Field.TYPE_UINT64, False, serialization_strategy.UIntEncoder),
        (type_pb2.Field.TYPE_BOOL, False, serialization_strategy.BoolEncoder),
        (type_pb2.Field.TYPE_STRING, False, serialization_strategy.StringEncoder),
    ],
)
def test___serialization_strategy___get_encoder___returns_expected_encoder(
    type, is_repeated, expected_encoder
):
    """Validate if proper encoder is returned.

    Args:
    ----
        type (type_pb2.Field.): gRPC type.
        is_repeated (bool): Represents if the parameter is array or scalar. True if array.
        expected_encoder (Callable): Callable expected to be returned for the type and is_repeated.

    """
    encoder = serialization_strategy.Context.get_encoder(type, is_repeated)

    assert encoder == expected_encoder


@pytest.mark.parametrize(
    "type,is_repeated,expected_decoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, serialization_strategy.FloatDecoder),
        (type_pb2.Field.TYPE_DOUBLE, False, serialization_strategy.DoubleDecoder),
        (type_pb2.Field.TYPE_INT32, False, serialization_strategy.Int32Decoder),
        (type_pb2.Field.TYPE_INT64, False, serialization_strategy.Int64Decoder),
        (type_pb2.Field.TYPE_UINT32, False, serialization_strategy.UInt32Decoder),
        (type_pb2.Field.TYPE_UINT64, False, serialization_strategy.UInt64Decoder),
        (type_pb2.Field.TYPE_BOOL, False, serialization_strategy.BoolDecoder),
        (type_pb2.Field.TYPE_STRING, False, serialization_strategy.StringDecoder),
    ],
)
def test___serialization_strategy___get_decoder___returns_expected_decoder(
    type, is_repeated, expected_decoder
):
    """Validate if proper decoder is returned.

    Args:
    ----
        type (type_pb2.Field.): gRPC type.
        is_repeated (bool): Represents if the parameter is array or scalar. True if array.
        expected_decoder (Callable): Callable expected to be returned for the type and is_repeated.

    """
    decoder = serialization_strategy.Context.get_decoder(type, is_repeated)

    assert decoder == expected_decoder


@pytest.mark.parametrize(
    "type,is_repeated,expected_default_value",
    [
        (type_pb2.Field.TYPE_FLOAT, False, 0.0),
        (type_pb2.Field.TYPE_DOUBLE, False, 0.0),
        (type_pb2.Field.TYPE_INT32, False, 0),
        (type_pb2.Field.TYPE_INT64, False, 0),
        (type_pb2.Field.TYPE_UINT32, False, 0),
        (type_pb2.Field.TYPE_UINT64, False, 0),
        (type_pb2.Field.TYPE_BOOL, False, False),
        (type_pb2.Field.TYPE_STRING, False, ""),
    ],
)
def test___serialization_strategy___get_default_value___returns_type_defaults(
    type, is_repeated, expected_default_value
):
    """Validate if the type default is returned.

    Args:
    ----
        type (type_pb2.Field.): gRPC type.
        is_repeated (bool): Represents if the parameter is array or scalar. True if array.
        expected_default_value (Callable): Type default value.

    """
    default_value = serialization_strategy.Context.get_type_default(type, is_repeated)

    assert default_value == expected_default_value

"""Contains tests to validate the serializationstrategy.py. """
import pytest
from google.protobuf import type_pb2

from ni_measurement_service._internal.parameter import serializationstrategy


@pytest.mark.parametrize(
    "type,is_repeated,expected_encoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, serializationstrategy.FloatEncoder),
        (type_pb2.Field.TYPE_DOUBLE, False, serializationstrategy.DoubleEncoder),
        (type_pb2.Field.TYPE_INT32, False, serializationstrategy.IntEncoder),
        (type_pb2.Field.TYPE_INT64, False, serializationstrategy.IntEncoder),
        (type_pb2.Field.TYPE_UINT32, False, serializationstrategy.UIntEncoder),
        (type_pb2.Field.TYPE_UINT64, False, serializationstrategy.UIntEncoder),
        (type_pb2.Field.TYPE_BOOL, False, serializationstrategy.BoolEncoder),
        (type_pb2.Field.TYPE_STRING, False, serializationstrategy.StringEncoder),
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
    encoder = serializationstrategy.Context.get_encoder(type, is_repeated)

    assert encoder == expected_encoder


@pytest.mark.parametrize(
    "type,is_repeated,expected_decoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, serializationstrategy.FloatDecoder),
        (type_pb2.Field.TYPE_DOUBLE, False, serializationstrategy.DoubleDecoder),
        (type_pb2.Field.TYPE_INT32, False, serializationstrategy.Int32Decoder),
        (type_pb2.Field.TYPE_INT64, False, serializationstrategy.Int64Decoder),
        (type_pb2.Field.TYPE_UINT32, False, serializationstrategy.UInt32Decoder),
        (type_pb2.Field.TYPE_UINT64, False, serializationstrategy.UInt64Decoder),
        (type_pb2.Field.TYPE_BOOL, False, serializationstrategy.BoolDecoder),
        (type_pb2.Field.TYPE_STRING, False, serializationstrategy.StringDecoder),
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
    decoder = serializationstrategy.Context.get_decoder(type, is_repeated)

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
    default_value = serializationstrategy.Context.get_type_default(type, is_repeated)

    assert default_value == expected_default_value

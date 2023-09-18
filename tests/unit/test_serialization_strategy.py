"""Contains tests to validate the serializationstrategy.py. """
import pytest
from google.protobuf import type_pb2

from ni_measurementlink_service._internal.parameter import serialization_strategy
from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2


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
        (type_pb2.Field.TYPE_ENUM, False, serialization_strategy.IntEncoder),
        (type_pb2.Field.TYPE_MESSAGE, False, serialization_strategy.MessageEncoder),
    ],
)
def test___serialization_strategy___get_encoder___returns_expected_encoder(
    type, is_repeated, expected_encoder
):
    encoder = serialization_strategy.get_encoder(type, is_repeated)

    assert encoder == expected_encoder


@pytest.mark.parametrize(
    "type,is_repeated,message_type,expected_decoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, "", serialization_strategy.FloatDecoder),
        (type_pb2.Field.TYPE_DOUBLE, False, "", serialization_strategy.DoubleDecoder),
        (type_pb2.Field.TYPE_INT32, False, "", serialization_strategy.Int32Decoder),
        (type_pb2.Field.TYPE_INT64, False, "", serialization_strategy.Int64Decoder),
        (type_pb2.Field.TYPE_UINT32, False, "", serialization_strategy.UInt32Decoder),
        (type_pb2.Field.TYPE_UINT64, False, "", serialization_strategy.UInt64Decoder),
        (type_pb2.Field.TYPE_BOOL, False, "", serialization_strategy.BoolDecoder),
        (type_pb2.Field.TYPE_STRING, False, "", serialization_strategy.StringDecoder),
        (type_pb2.Field.TYPE_ENUM, False, "", serialization_strategy.Int32Decoder),
        (
            type_pb2.Field.TYPE_MESSAGE,
            False,
            xydata_pb2.DoubleXYData.DESCRIPTOR.full_name,
            serialization_strategy.XYDataDecoder,
        ),
    ],
)
def test___serialization_strategy___get_decoder___returns_expected_decoder(
    type, is_repeated, message_type, expected_decoder
):
    decoder = serialization_strategy.get_decoder(type, is_repeated, message_type)

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
        (type_pb2.Field.TYPE_ENUM, False, 0),
        (type_pb2.Field.TYPE_MESSAGE, False, None),
    ],
)
def test___serialization_strategy___get_default_value___returns_type_defaults(
    type, is_repeated, expected_default_value
):
    default_value = serialization_strategy.get_type_default(type, is_repeated)

    assert default_value == expected_default_value

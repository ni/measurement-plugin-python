import pytest
from ni_measurement_service._internal.parameter import serializationstrategy
from google.protobuf import type_pb2


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
def test__serialization_strategy__get_encoder__returns_expected_encoder(
    type, is_repeated, expected_encoder
):
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
def test__serialization_strategy__get_decoder__returns_expected_decoder(
    type, is_repeated, expected_decoder
):
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
def test__serialization_strategy__get_default_value__returns_type_defaults(
    type, is_repeated, expected_default_value
):
    default_value = serializationstrategy.Context.get_type_default(type, is_repeated)

    assert default_value == expected_default_value

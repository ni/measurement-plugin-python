"""Contains tests to validate the serializationstrategy.py. """

import pytest
from google.protobuf import type_pb2

from ni_measurement_plugin_sdk_service._internal.parameter import (
    decoder_strategy,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    xydata_pb2,
)


@pytest.mark.parametrize(
    "type,is_repeated,message_type,expected_decoder",
    [
        (type_pb2.Field.TYPE_FLOAT, False, "", decoder_strategy.FloatDecoder),
        (type_pb2.Field.TYPE_DOUBLE, False, "", decoder_strategy.DoubleDecoder),
        (type_pb2.Field.TYPE_INT32, False, "", decoder_strategy.Int32Decoder),
        (type_pb2.Field.TYPE_INT64, False, "", decoder_strategy.Int64Decoder),
        (type_pb2.Field.TYPE_UINT32, False, "", decoder_strategy.UInt32Decoder),
        (type_pb2.Field.TYPE_UINT64, False, "", decoder_strategy.UInt64Decoder),
        (type_pb2.Field.TYPE_BOOL, False, "", decoder_strategy.BoolDecoder),
        (type_pb2.Field.TYPE_STRING, False, "", decoder_strategy.StringDecoder),
        (type_pb2.Field.TYPE_ENUM, False, "", decoder_strategy.Int32Decoder),
        (
            type_pb2.Field.TYPE_MESSAGE,
            False,
            xydata_pb2.DoubleXYData.DESCRIPTOR.full_name,
            decoder_strategy.XYDataDecoder,
        ),
        (
            type_pb2.Field.TYPE_MESSAGE,
            True,
            xydata_pb2.DoubleXYData.DESCRIPTOR.full_name,
            decoder_strategy.XYDataArrayDecoder,
        ),
    ],
)
def test___decoder_strategy___get_decoder___returns_expected_decoder(
    type, is_repeated, message_type, expected_decoder
):
    decoder = decoder_strategy.get_decoder(type, is_repeated, message_type)

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
        (type_pb2.Field.TYPE_MESSAGE, True, []),
    ],
)
def test___decoder_strategy___get_default_value___returns_type_defaults(
    type, is_repeated, expected_default_value
):
    default_value = decoder_strategy.get_type_default(type, is_repeated)

    assert default_value == expected_default_value

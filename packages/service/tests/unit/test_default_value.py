"""Contains tests to validate the serializationstrategy.py."""

import pytest
from google.protobuf import type_pb2

from ni_measurement_plugin_sdk_service._internal.parameter import (
    _get_type,
)


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
def test___get_default_value___returns_type_defaults(type, is_repeated, expected_default_value):
    test_default_value = _get_type.get_type_default(type, is_repeated)

    assert test_default_value == expected_default_value

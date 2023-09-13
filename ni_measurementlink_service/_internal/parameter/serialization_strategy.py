"""Serialization Strategy."""
from __future__ import annotations

import sys
import typing
from typing import Any, Callable, Dict, Optional, cast

from google.protobuf import type_pb2
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.internal import decoder, encoder
from google.protobuf.message import Message

if typing.TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

Key: TypeAlias = FieldDescriptor
WriteFunction: TypeAlias = Callable[[bytes], int]
Encoder: TypeAlias = Callable[[WriteFunction, bytes, bool], int]
PartialEncoderConstructor: TypeAlias = Callable[[int], Encoder]
EncoderConstructor: TypeAlias = Callable[[int, bool, bool], Encoder]

Decoder: TypeAlias = Callable[[memoryview, int, int, Message, Dict[Key, Any]], int]
PartialDecoderConstructor: TypeAlias = Callable[[int, Key], Decoder]
NewDefault: TypeAlias = Callable[[Message], Message]
DecoderConstructor: TypeAlias = Callable[[int, bool, bool, Key, NewDefault], Decoder]


def _scalar_encoder(encoder: EncoderConstructor) -> PartialEncoderConstructor:
    """Constructs a scalar encoder constructor.

    Takes a field index and returns an Encoder.

    This class returns the Encoder with is_repeated set to False
    and is_packed set to False.
    """

    def scalar_encoder(field_index: int) -> Encoder:
        is_repeated = False
        is_packed = False
        return encoder(field_index, is_repeated, is_packed)

    return scalar_encoder


def _vector_encoder(
    encoder: EncoderConstructor, is_packed: bool = True
) -> PartialEncoderConstructor:
    """Constructs a vector (array) encoder constructor.

    Takes a field index and returns an Encoder.

    This class returns the Encoder with is_repeated set to True
    and is_packed defaulting to True.
    """

    def vector_encoder(field_index: int) -> Encoder:
        is_repeated = True
        return encoder(field_index, is_repeated, is_packed)

    return vector_encoder


def _scalar_decoder(decoder: DecoderConstructor) -> PartialDecoderConstructor:
    """Constructs a scalar decoder constructor.

    Takes a field index and a key and returns a Decoder.

    This class returns the Decoder with is_repeated set to False
    and is_packed set to False.
    """

    def _unsupported_new_default(message: Optional[Message]) -> Any:
        raise NotImplementedError(
            "This function should not be called. Verify that you are using up-to-date and compatible versions of the ni-measurementlink-service and protobuf packages."
        )

    def scalar_decoder(field_index: int, key: Key) -> Decoder:
        is_repeated = False
        is_packed = False
        return decoder(field_index, is_repeated, is_packed, key, _unsupported_new_default)

    return scalar_decoder


def _vector_decoder(
    decoder: DecoderConstructor, is_packed: bool = True
) -> PartialDecoderConstructor:
    """Constructs a vector (array) decoder constructor.

    Takes a field index and a key and returns a Decoder.

    This class returns the Decoder with is_repeated set to True
    and is_packed defaulting to True.
    """

    def _new_default(unused_message: Optional[Message] = None) -> Any:
        return []

    def vector_decoder(field_index: int, key: Key) -> Decoder:
        is_repeated = True
        return decoder(field_index, is_repeated, is_packed, key, _new_default)

    return vector_decoder


# Cast works around this issue in typeshed
# https://github.com/python/typeshed/issues/10695
FloatEncoder = _scalar_encoder(cast(EncoderConstructor, encoder.FloatEncoder))
DoubleEncoder = _scalar_encoder(cast(EncoderConstructor, encoder.DoubleEncoder))
IntEncoder = _scalar_encoder(cast(EncoderConstructor, encoder.Int32Encoder))
UIntEncoder = _scalar_encoder(cast(EncoderConstructor, encoder.UInt32Encoder))
BoolEncoder = _scalar_encoder(encoder.BoolEncoder)
StringEncoder = _scalar_encoder(encoder.StringEncoder)

FloatArrayEncoder = _vector_encoder(cast(EncoderConstructor, encoder.FloatEncoder))
DoubleArrayEncoder = _vector_encoder(cast(EncoderConstructor, encoder.DoubleEncoder))
IntArrayEncoder = _vector_encoder(cast(EncoderConstructor, encoder.Int32Encoder))
UIntArrayEncoder = _vector_encoder(cast(EncoderConstructor, encoder.UInt32Encoder))
BoolArrayEncoder = _vector_encoder(encoder.BoolEncoder)
StringArrayEncoder = _vector_encoder(encoder.StringEncoder, is_packed=False)

# Cast works around this issue in typeshed
# https://github.com/python/typeshed/issues/10697
FloatDecoder = _scalar_decoder(cast(DecoderConstructor, decoder.FloatDecoder))
DoubleDecoder = _scalar_decoder(cast(DecoderConstructor, decoder.DoubleDecoder))
Int32Decoder = _scalar_decoder(cast(DecoderConstructor, decoder.Int32Decoder))
UInt32Decoder = _scalar_decoder(cast(DecoderConstructor, decoder.UInt32Decoder))
Int64Decoder = _scalar_decoder(cast(DecoderConstructor, decoder.Int64Decoder))
UInt64Decoder = _scalar_decoder(cast(DecoderConstructor, decoder.UInt64Decoder))
BoolDecoder = _scalar_decoder(cast(DecoderConstructor, decoder.BoolDecoder))
StringDecoder = _scalar_decoder(cast(DecoderConstructor, decoder.StringDecoder))

FloatArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.FloatDecoder))
DoubleArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.DoubleDecoder))
Int32ArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.Int32Decoder))
UInt32ArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.UInt32Decoder))
Int64ArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.Int64Decoder))
UInt64ArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.UInt64Decoder))
BoolArrayDecoder = _vector_decoder(cast(DecoderConstructor, decoder.BoolDecoder))
StringArrayDecoder = _vector_decoder(
    cast(DecoderConstructor, decoder.StringDecoder), is_packed=False
)


_FIELD_TYPE_TO_ENCODER_MAPPING = {
    type_pb2.Field.TYPE_FLOAT: (FloatEncoder, FloatArrayEncoder),
    type_pb2.Field.TYPE_DOUBLE: (DoubleEncoder, DoubleArrayEncoder),
    type_pb2.Field.TYPE_INT32: (IntEncoder, IntArrayEncoder),
    type_pb2.Field.TYPE_INT64: (IntEncoder, IntArrayEncoder),
    type_pb2.Field.TYPE_UINT32: (UIntEncoder, UIntArrayEncoder),
    type_pb2.Field.TYPE_UINT64: (UIntEncoder, UIntArrayEncoder),
    type_pb2.Field.TYPE_BOOL: (BoolEncoder, BoolArrayEncoder),
    type_pb2.Field.TYPE_STRING: (StringEncoder, StringArrayEncoder),
    type_pb2.Field.TYPE_ENUM: (IntEncoder, IntArrayEncoder),
}

_FIELD_TYPE_TO_DECODER_MAPPING = {
    type_pb2.Field.TYPE_FLOAT: (FloatDecoder, FloatArrayDecoder),
    type_pb2.Field.TYPE_DOUBLE: (DoubleDecoder, DoubleArrayDecoder),
    type_pb2.Field.TYPE_INT32: (Int32Decoder, Int32ArrayDecoder),
    type_pb2.Field.TYPE_INT64: (Int64Decoder, Int64ArrayDecoder),
    type_pb2.Field.TYPE_UINT32: (UInt32Decoder, UInt32ArrayDecoder),
    type_pb2.Field.TYPE_UINT64: (UInt64Decoder, UInt64ArrayDecoder),
    type_pb2.Field.TYPE_BOOL: (BoolDecoder, BoolArrayDecoder),
    type_pb2.Field.TYPE_STRING: (StringDecoder, StringArrayDecoder),
    type_pb2.Field.TYPE_ENUM: (Int32Decoder, Int32ArrayDecoder),
}

_TYPE_DEFAULT_MAPPING = {
    type_pb2.Field.TYPE_FLOAT: float(),
    type_pb2.Field.TYPE_DOUBLE: float(),
    type_pb2.Field.TYPE_INT32: int(),
    type_pb2.Field.TYPE_INT64: int(),
    type_pb2.Field.TYPE_UINT32: int(),
    type_pb2.Field.TYPE_UINT64: int(),
    type_pb2.Field.TYPE_BOOL: bool(),
    type_pb2.Field.TYPE_STRING: str(),
    type_pb2.Field.TYPE_ENUM: int(),
}


def get_encoder(type: type_pb2.Field.Kind.ValueType, repeated: bool) -> PartialEncoderConstructor:
    """Get the appropriate partial encoder constructor for the specified type.

    A scalar or vector constructor is returned based on the 'repeated' parameter.
    """
    if type not in _FIELD_TYPE_TO_ENCODER_MAPPING:
        raise ValueError(f"Error can not encode type '{type}'")
    scalar, array = _FIELD_TYPE_TO_ENCODER_MAPPING[type]
    if repeated:
        return array
    return scalar


def get_decoder(type: type_pb2.Field.Kind.ValueType, repeated: bool) -> PartialDecoderConstructor:
    """Get the appropriate partial decoder constructor for the specified type.

    A scalar or vector constructor is returned based on the 'repeated' parameter.
    """
    if type not in _FIELD_TYPE_TO_DECODER_MAPPING:
        raise ValueError(f"Error can not decode type '{type}'")
    scalar, array = _FIELD_TYPE_TO_DECODER_MAPPING[type]
    if repeated:
        return array
    return scalar


def get_type_default(type: type_pb2.Field.Kind.ValueType, repeated: bool) -> Any:
    """Get the default value for the give type."""
    if repeated:
        return list()
    type_default_value = _TYPE_DEFAULT_MAPPING.get(type)
    return type_default_value

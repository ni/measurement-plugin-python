"""Serialization Strategy."""

from typing import Any, Callable

from google.protobuf import type_pb2
from google.protobuf.internal import decoder
from google.protobuf.internal import encoder


def _scalar_encoder(encoder) -> Callable[[int], Callable]:
    """Abstract Specific Encoder(Callable) as Scalar Encoder Callable that takes in field index.

    Args
    ----
       encoder (Callable[[int, bool, bool], Callable]): Specific encoder that takes in
       field_index, is_repeated, is_packed and returns the Low-level Encode Callable.

    Returns
    -------
        Callable[[int],Callable]: Callable Encoder for scalar types that takes
        in field_index and returns the Low-level Encode Callable.

    """

    def scalar_encoder(field_index):
        is_repeated = False
        is_packed = False
        return encoder(field_index, is_repeated, is_packed)

    return scalar_encoder


def _vector_encoder(encoder, is_packed=True) -> Callable[[int], Callable]:
    """Abstract Specific Encoder(Callable) as Vector Encoder Callable that takes in field index.

    Args
    ----
       encoder (Callable[[int, bool, bool], Callable]): Specific encoder(Callable) that takes in
       field_index, is_repeated, is_packed and returns the Low-level Encode Callable.

       is_packed (bool, optional): Represents if the encoder supports packed type. Defaults to True.

    Returns
    -------
        Callable[[int],Callable]: Callable Encoder for 1D Array types that takes in
        field_index and returns the Low-level Encode Callable.

    """

    def vector_encoder(field_index):
        is_repeated = True
        return encoder(field_index, is_repeated, is_packed)

    return vector_encoder


def _scalar_decoder(decoder) -> Callable[[int, str], Callable]:
    """Abstract Specific Decoder(Callable) as Scalar Decoder Callable that takes in field index,key.

    Args
    ----
        decoder (Callable[[int, bool, bool], Callable]): Specific decoder(Callable) that takes in
        field_index, is_repeated, is_packed,  key, new_default and
        returns the Low-level Decode Callable.

    Returns
    -------
        Callable[[int,str],Callable]: Callable Decoder for scalar types that takes in
        field_index, key and returns the Low-level Decode Callable.

    """

    def scalar_decoder(field_index, key):
        is_repeated = False
        is_packed = False
        return decoder(field_index, is_repeated, is_packed, key, None)

    return scalar_decoder


def _vector_decoder(decoder, is_packed=True) -> Callable[[int, str], Callable]:
    """Abstract Specific Decoder(Callable) as Vector Decoder Callable that takes in field index,key.

    Args
    ----
        decoder (Callable[[int, bool, bool], Callable]): Specific decoder(Callable) that takes in
        field_index, is_repeated, is_packed,  key, new_default and
        returns the Low-level Decode Callable.

        is_packed (bool, optional): Represents if the decoder supports packed type.
        Defaults to True.

    Returns
    -------
        Callable[[int,str],Callable]: Callable Decoder for 1D Array types that takes in
        field_index , key and returns the Low-level Decode Callable.

    """

    def _new_default(unused_message=None):
        return []

    def vector_decoder(field_index, key):
        is_repeated = True
        return decoder(field_index, is_repeated, is_packed, key, _new_default)

    return vector_decoder


FloatEncoder = _scalar_encoder(encoder.FloatEncoder)
DoubleEncoder = _scalar_encoder(encoder.DoubleEncoder)
IntEncoder = _scalar_encoder(encoder.Int32Encoder)
UIntEncoder = _scalar_encoder(encoder.UInt32Encoder)
BoolEncoder = _scalar_encoder(encoder.BoolEncoder)
StringEncoder = _scalar_encoder(encoder.StringEncoder)

FloatArrayEncoder = _vector_encoder(encoder.FloatEncoder)
DoubleArrayEncoder = _vector_encoder(encoder.DoubleEncoder)
IntArrayEncoder = _vector_encoder(encoder.Int32Encoder)
UIntArrayEncoder = _vector_encoder(encoder.UInt32Encoder)
BoolArrayEncoder = _vector_encoder(encoder.BoolEncoder)
StringArrayEncoder = _vector_encoder(encoder.StringEncoder, is_packed=False)


FloatDecoder = _scalar_decoder(decoder.FloatDecoder)
DoubleDecoder = _scalar_decoder(decoder.DoubleDecoder)
Int32Decoder = _scalar_decoder(decoder.Int32Decoder)
UInt32Decoder = _scalar_decoder(decoder.UInt32Decoder)
Int64Decoder = _scalar_decoder(decoder.Int64Decoder)
UInt64Decoder = _scalar_decoder(decoder.UInt64Decoder)
BoolDecoder = _scalar_decoder(decoder.BoolDecoder)
StringDecoder = _scalar_decoder(decoder.StringDecoder)

FloatArrayDecoder = _vector_decoder(decoder.FloatDecoder)
DoubleArrayDecoder = _vector_decoder(decoder.DoubleDecoder)
Int32ArrayDecoder = _vector_decoder(decoder.Int32Decoder)
UInt32ArrayDecoder = _vector_decoder(decoder.UInt32Decoder)
Int64ArrayDecoder = _vector_decoder(decoder.Int64Decoder)
UInt64ArrayDecoder = _vector_decoder(decoder.UInt64Decoder)
BoolArrayDecoder = _vector_decoder(decoder.BoolDecoder)
StringArrayDecoder = _vector_decoder(decoder.StringDecoder, is_packed=False)


class Context:
    """Strategy context."""

    _FIELD_TYPE_TO_ENCODER_MAPPING = {
        type_pb2.Field.TYPE_FLOAT: (FloatEncoder, FloatArrayEncoder),
        type_pb2.Field.TYPE_DOUBLE: (DoubleEncoder, DoubleArrayEncoder),
        type_pb2.Field.TYPE_INT32: (IntEncoder, IntArrayEncoder),
        type_pb2.Field.TYPE_INT64: (IntEncoder, IntArrayEncoder),
        type_pb2.Field.TYPE_UINT32: (UIntEncoder, UIntArrayEncoder),
        type_pb2.Field.TYPE_UINT64: (UIntEncoder, UIntArrayEncoder),
        type_pb2.Field.TYPE_BOOL: (BoolEncoder, BoolArrayEncoder),
        type_pb2.Field.TYPE_STRING: (StringEncoder, StringArrayEncoder),
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
    }

    @staticmethod
    def get_encoder(
        type: type_pb2.Field.Kind.ValueType, repeated: bool
    ) -> Callable[[int], Callable]:
        """Get the Scalar Encoder or Vector Encoder for the specified type based on repeated bool.

        Args
        ----
            type (type_pb2.Field.Kind.ValueType): Type of the Parameter.

            repeated (bool): Boolean that represents if the Parameter is repeated or not.

        Raises
        ------
            Exception: If the specified type is not supported.

        Returns
        -------
            Callable[[int], Callable]: ScalarEncoder or VectorEncoder.

        """
        if type not in Context._FIELD_TYPE_TO_ENCODER_MAPPING:
            raise Exception(f"Error can not encode type '{type}'")
        scalar, array = Context._FIELD_TYPE_TO_ENCODER_MAPPING[type]
        if repeated:
            return array
        return scalar

    @staticmethod
    def get_decoder(
        type: type_pb2.Field.Kind.ValueType, repeated: bool
    ) -> Callable[[int, str], Callable]:
        """Get the Scalar Decoder or Vector Decoder for the specified type based on repeated bool.

        Args
        ----
            type (type_pb2.Field.Kind.ValueType): Type of the Parameter.

            repeated (bool): Boolean that represents if the Parameter is repeated or not.

        Raises
        ------
            Exception: If the specified type is not supported.

        Returns
        -------
            Callable[[int], Callable]: ScalarDecoder or VectorDecoder.

        """
        if type not in Context._FIELD_TYPE_TO_DECODER_MAPPING:
            raise Exception(f"Error can not decode type '{type}'")
        scalar, array = Context._FIELD_TYPE_TO_DECODER_MAPPING[type]
        if repeated:
            return array
        return scalar

    @staticmethod
    def get_type_default(type: type_pb2.Field.Kind.ValueType, repeated: bool) -> Any:
        """Get the Type default.

        Args
        ----
            type (type_pb2.Field.Kind.ValueType): Type of the Parameter.

            repeated (bool): Boolean that represents if the Parameter is repeated or not.

        Returns
        -------
            Any: Default value.

        """
        if repeated:
            return list()
        type_default_value = Context._TYPE_DEFAULT_MAPPING.get(type)
        return type_default_value

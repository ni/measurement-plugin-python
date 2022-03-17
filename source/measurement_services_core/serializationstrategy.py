import google.protobuf.type_pb2 as type_pb2
from google.protobuf.internal import encoder
from google.protobuf.internal import decoder


def _ScalarEncoder(encoder):
    def ScalarEncoder(field_index):
        is_repeated = False
        is_packed = False
        return encoder(field_index, is_repeated, is_packed)

    return ScalarEncoder


def _VectorEncoder(encoder):
    def VectorEncoder(field_index):
        is_repeated = True
        is_packed = True
        return encoder(field_index, is_repeated, is_packed)

    return VectorEncoder


def _ScalarDecoder(decoder):
    def ScalarDecoder(field_index, name):
        is_repeated = False
        is_packed = False
        return decoder(field_index, is_repeated, is_packed, name, None)

    return ScalarDecoder


def _VectorDecoder(decoder):
    def _new_default(unused_message=None):
        return []

    def VectorDecoder(field_index, name):
        is_repeated = True
        is_packed = True
        return decoder(field_index, is_repeated, is_packed, name, _new_default)

    return VectorDecoder


FloatEncoder = _ScalarEncoder(encoder.FloatEncoder)
DoubleEncoder = _ScalarEncoder(encoder.DoubleEncoder)
IntEncoder = _ScalarEncoder(encoder.Int32Encoder)
UIntEncoder = _ScalarEncoder(encoder.UInt32Encoder)
BoolEncoder = _ScalarEncoder(encoder.BoolEncoder)
StringEncoder = _ScalarEncoder(encoder.StringEncoder)

FloatArrayEncoder = _VectorEncoder(encoder.FloatEncoder)
DoubleArrayEncoder = _VectorEncoder(encoder.DoubleEncoder)
IntArrayEncoder = _VectorEncoder(encoder.Int32Encoder)
UIntArrayEncoder = _VectorEncoder(encoder.UInt32Encoder)
BoolArrayEncoder = _VectorEncoder(encoder.BoolEncoder)
StringArrayEncoder = _VectorEncoder(encoder.StringEncoder)


FloatDecoder = _ScalarDecoder(decoder.FloatDecoder)
DoubleDecoder = _ScalarDecoder(decoder.DoubleDecoder)
Int32Decoder = _ScalarDecoder(decoder.Int32Decoder)
UInt32Decoder = _ScalarDecoder(decoder.UInt32Decoder)
Int64Decoder = _ScalarDecoder(decoder.Int64Decoder)
UInt64Decoder = _ScalarDecoder(decoder.UInt64Decoder)
BoolDecoder = _ScalarDecoder(decoder.BoolDecoder)
StringDecoder = _ScalarDecoder(decoder.StringDecoder)

FloatArrayDecoder = _VectorDecoder(decoder.FloatDecoder)
DoubleArrayDecoder = _VectorDecoder(decoder.DoubleDecoder)
Int32ArrayDecoder = _VectorDecoder(decoder.Int32Decoder)
UInt32ArrayDecoder = _VectorDecoder(decoder.UInt32Decoder)
Int64ArrayDecoder = _VectorDecoder(decoder.Int64Decoder)
UInt64ArrayDecoder = _VectorDecoder(decoder.UInt64Decoder)
BoolArrayDecoder = _VectorDecoder(decoder.BoolDecoder)
StringArrayDecoder = _VectorDecoder(decoder.StringDecoder)


class Context:
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

    def get_encoder(type: type_pb2.Field, repeated: bool):
        if type not in Context._FIELD_TYPE_TO_ENCODER_MAPPING:
            raise Exception(f"Error can not encode type '{type}'")
        (scalar, array) = Context._FIELD_TYPE_TO_ENCODER_MAPPING.get(type)
        if repeated:
            return array
        return scalar

    def get_decoder(type: type_pb2.Field, repeated: bool):
        if type not in Context._FIELD_TYPE_TO_DECODER_MAPPING:
            raise Exception(f"Error can not decode type '{type}'")
        (scalar, array) = Context._FIELD_TYPE_TO_DECODER_MAPPING.get(type)
        if repeated:
            return array
        return scalar

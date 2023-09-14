import struct
from typing import Any, Dict

from google.protobuf.internal import encoder, wire_format
from google.protobuf.message import Message

from ni_measurementlink_service._internal.parameter._serializer_types import (
    Decoder,
    Encoder,
    Key,
    NewDefault,
)


def _inner_message_encoder(field_index: int, is_repeated: bool, is_packed: bool) -> Encoder:
    """Mimics google.protobuf.internal.MessageEncoder.

    See EncodeField:
    https://github.com/protocolbuffers/protobuf/blob/0b817d46d4ca1977d3dccf2442aeee3c9e98e3a1/python/google/protobuf/internal/encoder.py#L765C15-L765C15
    """
    tag = encoder.TagBytes(field_index, wire_format.WIRETYPE_LENGTH_DELIMITED)
    encode_varint = _varint_encoder()

    def _encode_message(write, value, deterministic):
        write(tag)
        bytes = value.SerializeToString()
        encode_varint(write, len(bytes), deterministic)
        write(bytes)

    return _encode_message


def _varint_encoder():
    """Return an encoder for a basic varint value (does not include tag).

    From google.protobuf.internal.encoder.py _VarintEncoder
    """
    local_int2byte = struct.Struct(">B").pack

    def encode_varint(write, value, unused_deterministic=None):
        bits = value & 0x7F
        value >>= 7
        while value:
            write(local_int2byte(0x80 | bits))
            bits = value & 0x7F
            value >>= 7
        return write(local_int2byte(bits))

    return encode_varint


def _inner_message_decoder(
    field_index: int, is_repeated: bool, is_packed: bool, key: Key, new_default: NewDefault
) -> Decoder:
    """Based on google.protobuf.internal.MessageDecoder.

    See DecodeField
    """

    def _decode_message(
        buffer: memoryview, pos: int, end: int, message: Message, field_dict: Dict[Key, Any]
    ) -> int:
        decode_varint = _varint_decoder(mask=(1 << 64) - 1, result_type=int)
        value = field_dict.get(key)
        if value is None:
            value = field_dict.setdefault(key, new_default(message))
        # Read length.
        (size, pos) = decode_varint(buffer, pos)
        new_pos = pos + size
        value.ParseFromString(buffer[pos:new_pos])
        return new_pos

    return _decode_message


def _varint_decoder(mask, result_type):
    """Return an encoder for a basic varint value (does not include tag).

    Decoded values will be bitwise-anded with the given mask before being
    returned, e.g. to limit them to 32 bits.  The returned decoder does not
    take the usual "end" parameter -- the caller is expected to do bounds checking
    after the fact (often the caller can defer such checking until later).  The
    decoder returns a (value, new_pos) pair.

    From google.protobuf.internal.decoder.py _VarintDecoder
    """

    def decode_varint(buffer, pos):
        result = 0
        shift = 0
        while 1:
            b = buffer[pos]
            result |= (b & 0x7F) << shift
            pos += 1
            if not (b & 0x80):
                result &= mask
                result = result_type(result)
                return (result, pos)
            shift += 7
            if shift >= 64:
                raise ValueError("Too many bytes when decoding varint: {shift}")

    return decode_varint

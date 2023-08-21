import struct

from google.protobuf.internal import encoder, wire_format


def _inner_message_encoder(field_index):
    """Mimics google.protobuf.internal.MessageEncoder.

    See EncodeField:
    https://github.com/protocolbuffers/protobuf/blob/0b817d46d4ca1977d3dccf2442aeee3c9e98e3a1/python/google/protobuf/internal/encoder.py#L765C15-L765C15
    """
    tag = encoder.TagBytes(field_index, wire_format.WIRETYPE_LENGTH_DELIMITED)

    def _encode_message(write, value, deterministic):
        write(tag)
        bytes = value.SerializeToString()
        _encode_varint(write, len(bytes), deterministic)
        write(bytes)

    return _encode_message


_int2byte = struct.Struct(">B").pack


def _encode_varint(write, value, unused_deterministic=None):
    """Implementation from google.protobuf.internal EncodeVarint."""
    bits = value & 0x7F
    value >>= 7
    while value:
        write(_int2byte(0x80 | bits))
        bits = value & 0x7F
        value >>= 7
    return write(_int2byte(bits))


def _inner_message_decoder(field_index, is_repeated, is_packed, key, new_default):
    """Based on google.protobuf.internal.MessageDecoder.

    See DecodeField
    """

    def _convert_to_byte_string(memview):
        byte_str = memview.tobytes()
        return byte_str

    def _decode_message(buffer, pos, end, message, field_dict):
        value = field_dict.get(key)
        if value is None:
            value = field_dict.setdefault(key, new_default(message))
        # Read length.
        (size, pos) = _decode_varint(buffer, pos)
        new_pos = pos + size
        thestring = _convert_to_byte_string(buffer[pos:new_pos])
        value.ParseFromString(thestring)
        return new_pos

    return _decode_message


def _decode_varint(buffer, pos):
    """Implementation from google.protobuf.internal DecodeVarint."""
    mask = (1 << 64) - 1
    result_type = int
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

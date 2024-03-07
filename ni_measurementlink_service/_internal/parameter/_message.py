import struct
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from google.protobuf.internal import encoder, wire_format
from google.protobuf.message import Message

from ni_measurementlink_service._internal.parameter._serializer_types import (
    Decoder,
    Key,
    NewDefault,
    WriteFunction,
)


def _message_encoder_constructor(
    field_index: int, is_repeated: bool, is_packed: bool
) -> Callable[[WriteFunction, Union[Message, List[Message]], bool], int]:
    """Mimics google.protobuf.internal.MessageEncoder.

    This function was forked in order to call SerializeToString instead of _InternalSerialize.

    _InternalSerialize is only defined for the pure-Python protobuf implementation. Our child
    messages (like DoubleXYData) are defined in .proto files, so they use whichever protobuf
    implementation that google.protobuf.internal.api_implementation chooses (usually upb).
    """
    tag = encoder.TagBytes(field_index, wire_format.WIRETYPE_LENGTH_DELIMITED)
    encode_varint = _varint_encoder()

    if is_repeated:

        def _encode_repeated_message(
            write: WriteFunction, value: Union[Message, List[Message]], deterministic: bool
        ) -> int:
            bytes_written = 0
            for element in cast(List[Message], value):
                write(tag)
                bytes = element.SerializeToString()
                encode_varint(write, len(bytes), deterministic)
                bytes_written += write(bytes)
            return bytes_written

        return _encode_repeated_message
    else:

        def _encode_message(
            write: WriteFunction, value: Union[Message, List[Message]], deterministic: bool
        ) -> int:
            write(tag)
            bytes = cast(Message, value).SerializeToString()
            encode_varint(write, len(bytes), deterministic)
            return write(bytes)

        return _encode_message


def _varint_encoder() -> Callable[[WriteFunction, int, Optional[bool]], int]:
    """Return an encoder for a basic varint value (does not include tag).

    From google.protobuf.internal.encoder.py _VarintEncoder
    """
    local_int2byte = struct.Struct(">B").pack

    def encode_varint(
        write: WriteFunction, value: int, unused_deterministic: Optional[bool] = None
    ) -> int:
        bits = value & 0x7F
        value >>= 7
        while value:
            write(local_int2byte(0x80 | bits))
            bits = value & 0x7F
            value >>= 7
        return write(local_int2byte(bits))

    return encode_varint


def _message_decoder_constructor(
    field_index: int, is_repeated: bool, is_packed: bool, key: Key, new_default: NewDefault
) -> Decoder:
    """Mimics google.protobuf.internal.MessageDecoder.

    This function was forked in order to call ParseFromString instead of _InternalParse.

    _InternalParse is only defined for the pure-Python protobuf implementation. Our child messages
    (like DoubleXYData) are defined in .proto files, so they use whichever protobuf implementation
    that google.protobuf.internal.api_implementation chooses (usually upb).
    """
    if is_repeated:
        tag_bytes = encoder.TagBytes(field_index, wire_format.WIRETYPE_LENGTH_DELIMITED)
        tag_len = len(tag_bytes)

        def _decode_repeated_message(
            buffer: memoryview, pos: int, end: int, message: Message, field_dict: Dict[Key, Any]
        ) -> int:
            decode_varint = _varint_decoder(mask=(1 << 64) - 1, result_type=int)
            value = field_dict.get(key)
            if value is None:
                value = field_dict.setdefault(key, [])
            while 1:
                parsed_value = new_default(message)
                # Read length.
                (size, pos) = decode_varint(buffer, pos)
                new_pos = pos + size
                if new_pos > end:
                    raise ValueError("Error decoding a message. Message is truncated.")
                parsed_bytes = parsed_value.ParseFromString(buffer[pos:new_pos])
                if parsed_bytes != size:
                    raise ValueError("Parsed incorrect number of bytes.")
                value.append(parsed_value)
                # Predict that the next tag is another copy of the same repeated field.
                pos = new_pos + tag_len
                if buffer[new_pos:pos] != tag_bytes or new_pos == end:
                    # Prediction failed.  Return.
                    return new_pos

        return _decode_repeated_message
    else:

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
            if new_pos > end:
                raise ValueError("Error decoding a message. Message is truncated.")
            parsed_bytes = value.ParseFromString(buffer[pos:new_pos])
            if parsed_bytes != size:
                raise ValueError("Parsed incorrect number of bytes.")
            return new_pos

        return _decode_message


T = TypeVar("T", bound="int")


def _varint_decoder(mask: int, result_type: Type[T]) -> Callable[[memoryview, int], Tuple[T, int]]:
    """Return an encoder for a basic varint value (does not include tag).

    Decoded values will be bitwise-anded with the given mask before being
    returned, e.g. to limit them to 32 bits.  The returned decoder does not
    take the usual "end" parameter -- the caller is expected to do bounds checking
    after the fact (often the caller can defer such checking until later).  The
    decoder returns a (value, new_pos) pair.

    From google.protobuf.internal.decoder.py _VarintDecoder
    """

    def decode_varint(buffer: memoryview, pos: int) -> Tuple[T, int]:
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

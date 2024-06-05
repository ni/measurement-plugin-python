from __future__ import annotations

import sys
import typing
from typing import Any, Callable, Dict

from google.protobuf.descriptor import FieldDescriptor
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

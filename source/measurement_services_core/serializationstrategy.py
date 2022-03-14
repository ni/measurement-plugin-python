import google.protobuf.type_pb2 as type_pb2
from abc import abstractmethod
from google.protobuf.internal import encoder
from google.protobuf.internal import decoder


is_repeated_scalar = False
is_repeated_array = True
is_packed = True


class BaseStrategy:
    @abstractmethod
    def __new_default(self, message):
        pass

    @abstractmethod
    def encoder(self, field_index):
        pass

    @abstractmethod
    def decoder(self, field_index, name):
        pass


class DoubleStrategy(BaseStrategy):
    def __new_default(self, message):
        return 0.0

    def encoder(self, field_index: int):
        return encoder.DoubleEncoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.DoubleDecoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class DoubleArrayStrategy(BaseStrategy):
    def __new_default(self, message):
        return []

    def encoder(self, field_index: int):
        return encoder.DoubleEncoder(field_index, is_repeated_array, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.DoubleDecoder(
            field_index, is_repeated_array, is_packed, name, self.__new_default
        )


class BoolStrategy(BaseStrategy):
    def __new_default(self, message):
        return False

    def encoder(self, field_index: int):
        return encoder.BoolEncoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.BoolDecoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class StringStrategy(BaseStrategy):
    def __new_default(self, message):
        return ""

    def encoder(self, field_index: int):
        return encoder.StringEncoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.StringDecoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class FloatStrategy(BaseStrategy):
    def __new_default(self, message):
        return 0.0

    def encoder(self, field_index: int):
        return encoder.FloatEncoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.FloatDecoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class Int32Strategy(BaseStrategy):
    def __new_default(self, message):
        return 0

    def encoder(self, field_index: int):
        return encoder.Int32Encoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.Int32Decoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class Int64Strategy(BaseStrategy):
    def __new_default(self, message):
        return 0

    def encoder(self, field_index: int):
        return encoder.Int32Encoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.Int64Decoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class UInt32Strategy(BaseStrategy):
    def __new_default(self, message):
        return 0

    def encoder(self, field_index: int):
        return encoder.UInt32Encoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.UInt32Decoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class UInt64Strategy(BaseStrategy):
    def __new_default(self, message):
        return 0

    def encoder(self, field_index: int):
        return encoder.UInt32Encoder(field_index, is_repeated_scalar, is_packed)

    def decoder(self, field_index: int, name: str):
        return decoder.UInt64Decoder(
            field_index, is_repeated_scalar, is_packed, name, self.__new_default
        )


class Context:
    serialization_strategy_set = {
        type_pb2.Field.TYPE_DOUBLE: (
            DoubleStrategy(),
            DoubleArrayStrategy(),
        ),
        type_pb2.Field.TYPE_BOOL: (BoolStrategy(), None),
        type_pb2.Field.TYPE_INT32: (Int32Strategy(), None),
        type_pb2.Field.TYPE_INT64: (Int64Strategy(), None),
        type_pb2.Field.TYPE_UINT32: (UInt32Strategy(), None),
        type_pb2.Field.TYPE_UINT64: (UInt64Strategy(), None),
        type_pb2.Field.TYPE_STRING: (StringStrategy(), None),
    }

    def get_strategy(type: type_pb2.Field, repeated: bool) -> BaseStrategy:
        (scalar, array) = Context.serialization_strategy_set.get(type)
        if repeated:
            return array
        return scalar

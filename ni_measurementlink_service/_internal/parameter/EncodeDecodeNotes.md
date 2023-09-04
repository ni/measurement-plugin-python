From typeshed, here's the definition of an _Encoder:

```python
_Encoder: TypeAlias = Callable[[Callable[[bytes], int], bytes, bool], int]
``````

I put this as the return type for _scalar_encoder and _vector_encoder like so:
```python
def _scalar_encoder(encoder) -> Callable[[int], _Encoder]:
```

This works and mypy succeeds.

Now, what is the type of the parameter passed to _scalar_encoder? I.e. can we have a type hint here?
```python
def _scalar_encoder(encoder: WhatType)
```

Well, it takes a FloatEncoder, which according to typeshed is an _Encoder. However putting it as _Encoder gives these errors:

```shell
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:30: error: Argument 2 has incompatible type "bool"; expected "bytes"  [arg-type]
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:116: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"; expected "Callable[[Callable[[bytes], int], bytes, bool], int]"  [arg-type]     
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:117: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"; expected "Callable[[Callable[[bytes], int], bytes, bool], int]"  [arg-type]
```

So typeshed must be wrong about FloatEncoder

Maybe it's something like this:

```python
InnerEncoder: TypeAlias = Callable[[int, bool, bool], _Encoder]
def _scalar_encoder(encoder: InnerEncoder) -> Callable[[int], _Encoder]:
```

No, this doesn't work because of these errors (where we pass FloatEncoder, DoubleEncoder, Int32Encoder, UInt32Encoder; BoolEncoder and StringEncoder work fine with this type hint):
```bat
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:113: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[Callable[[bytes], int], bytes, bool], int]"; expected "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"  [arg-type]
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:114: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[Callable[[bytes], int], bytes, bool], int]"; expected "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"  [arg-type]
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:115: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[Callable[[bytes], int], bytes, bool], int]"; expected "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"  [arg-type]
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:116: error: Argument 1 to "_scalar_encoder" has incompatible type "Callable[[Callable[[bytes], int], bytes, bool], int]"; expected "Callable[[int, bool, bool], Callable[[Callable[[bytes], int], bytes, bool], int]]"  [arg-type]
```

What if we try a Union of these two:
```python
def _scalar_encoder(encoder: Union[InnerEncoder, _Encoder])
```

Gives this error:
```bat
ni_measurementlink_service\_internal\parameter\serialization_strategy.py:31: error: Argument 2 has incompatible type "bool"; expected "bytes"  [arg-type]
```
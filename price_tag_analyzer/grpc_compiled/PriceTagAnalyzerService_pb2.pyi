from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageChunk(_message.Message):
    __slots__ = ("content",)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: bytes
    def __init__(self, content: _Optional[bytes] = ...) -> None: ...

class Measure(_message.Message):
    __slots__ = ("amount", "unit")
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    amount: float
    unit: str
    def __init__(self, amount: _Optional[float] = ..., unit: _Optional[str] = ...) -> None: ...

class ImageInfo(_message.Message):
    __slots__ = ("product", "description", "price", "measure", "attributes")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PRODUCT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    MEASURE_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    product: str
    description: str
    price: float
    measure: Measure
    attributes: _containers.ScalarMap[str, str]
    def __init__(self, product: _Optional[str] = ..., description: _Optional[str] = ..., price: _Optional[float] = ..., measure: _Optional[_Union[Measure, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

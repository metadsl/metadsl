"""
Data representation of Python marshal serialization.

This was created to help debug why storing the `co_names` changes
the value of the marshaled bytes, i.e.:

```python
from marshal import dumps
c = compile("a", "<str>", "exec")
orig = dumps(c)
_ = c.co_names
new_ = dumps(c)
assert orig != new_
```

To debug this, we turn the marshalled bytes into a data representation,
to be able to understand them.

This is based off of reading `marshal.c`
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class MarshalledData:
    objs: List[MarshalledObject] 
    @classmethod
    def from_bytes(cls, b: bytes) -> MarshalledData:
        ...

    def to_bytes(self) -> bytes:
        ...


@dataclass
class MarshalledObject:
    # Whether this object is a ref
    ref: bool
    obj: 


@dataclass
class MarshalledNone:
    pass

MarshalledObject = List[MarshalledNone]
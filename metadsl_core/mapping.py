from __future__ import annotations
import typing
from metadsl import *
from metadsl_rewrite import *

from .strategies import *

__all__ = ["Mapping"]

K = typing.TypeVar("K")
V = typing.TypeVar("V")

class Mapping(Expression, typing.Generic[K, V]):
    """
    mapping from string to object
    """
    
    @expression
    def __getitem__(self, k: K) -> V:
        ...
    
    @expression
    def setitem(self, k: K, v: V) -> Mapping[K, V]:
        ...
    
    @expression
    @classmethod
    def empty(cls) -> Mapping[K, V]:
        ...

@register_ds
@rule
def mapping_getitem(k: K, v: V, other_k: K, m: Mapping[K, V]) -> R[V]:
    yield m.setitem(k, v)[k], v

    # Only recurse down if the keys are not equal
    def res():
        if k == other_k:
            raise NoMatch()
        return m[k]
    yield m.setitem(other_k, v)[k], res


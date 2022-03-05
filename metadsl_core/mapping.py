from __future__ import annotations
import typing
from metadsl import *
from metadsl_rewrite import *

from .strategies import *
from .pair import *

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
    def extend(self, m: Mapping[K, V]) -> Mapping[K, V]:
        ...

    @expression
    @classmethod
    def empty(cls) -> Mapping[K, V]:
        return cls.create()

    @expression
    @classmethod
    def create(cls, *items: Pair[K, V]) -> Mapping[K, V]:
        ...



register_ds(default_rule(Mapping.empty))

@register_ds
@rule
def mapping_create(k: K, other_k: K, v: V, items: typing.Sequence[Pair[K, V]]):
    yield Mapping[K, V].create(*items).setitem(k, v), Mapping[K, V].create(Pair.create(k, v), *items)


    def getitem_create_res():
        if k == other_k:
            return v
        return Mapping.create(*items)[k]
    
    yield Mapping.create(Pair.create(other_k, v), *items)[k], getitem_create_res

@register_ds
@rule
def mapping_extend(m: Mapping[K, V], k: K, other_k: K, v: V, l: typing.Sequence[Pair[K, V]], r: typing.Sequence[Pair[K, V]]):
    # Extending a create
    yield Mapping.create(*l).extend(Mapping.create(*r)), Mapping.create(*r, *l)

    # Setting an item on a mapping is the same as extending with that mapping
    yield m.setitem(k, v), m.extend(Mapping.create(Pair.create(k, v)))


    # We can combine two extensions, the later one should override
    yield m.extend(Mapping.create(*l)).extend(Mapping.create(*r)), Mapping.create(*r, *l)

    # Getting an item from an extend could work!
    def getitem_create_res():
        if k == other_k:
            return v
        return m.extend(Mapping.create(*l))[k]
    
    yield m.extend(Mapping.create(Pair.create(other_k, v), *l))[k], getitem_create_res





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


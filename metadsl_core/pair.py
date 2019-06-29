from __future__ import annotations
import typing

from metadsl import *
from .rules import *

__all__ = ["Pair"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


class Pair(Expression, typing.Generic[T, U]):
    @expression
    def left(self) -> T:
        ...

    @expression
    def right(self) -> U:
        ...

    @expression
    @classmethod
    def create(cls, left: T, right: U) -> Pair[T, U]:
        ...


@register
@rule
def pair_left(l: T, r: U) -> R[T]:
    """
    >>> execute_core(Pair.create(10, 20).left())
    10
    """
    return Pair.create(l, r).left(), l


@register
@rule
def pair_right(l: T, r: U) -> R[U]:
    """
    >>> execute_core(Pair.create(10, 20).right())
    20
    """
    return Pair.create(l, r).right(), r

from __future__ import annotations
import typing

from metadsl import *
from .rules import *

__all__ = ["Pair"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


class Pair(Expression, typing.Generic[T, U]):
    @expression  # type: ignore
    @property
    def left(self) -> T:
        ...

    @expression  # type: ignore
    @property
    def right(self) -> U:
        ...

    @expression
    def set_left(self, left: T) -> Pair[T, U]:
        ...

    @expression
    def set_right(self, right: U) -> Pair[T, U]:
        ...

    @expression
    @classmethod
    def create(cls, left: T, right: U) -> Pair[T, U]:
        ...

    @property
    def spread(self) -> typing.Tuple[T, U]:
        return self.left, self.right


@register  # type: ignore
@rule
def pair_left(l: T, r: U) -> R[T]:
    """
    >>> execute(Pair.create(10, 20).left)
    10
    """
    return Pair.create(l, r).left, l


@register  # type: ignore
@rule
def pair_right(l: T, r: U) -> R[U]:
    """
    >>> execute(Pair.create(10, 20).right)
    20
    """
    return Pair.create(l, r).right, r


@register  # type: ignore
@rule
def pair_set(l: T, r: U, new_l: T, new_r: U) -> R[Pair[T, U]]:
    """
    >>> execute(Pair.create(10, 20).set_left(5).left)
    5
    >>> execute(Pair.create(10, 20).set_left(5).right)
    20
    >>> execute(Pair.create(10, 20).set_right(5).left)
    10
    >>> execute(Pair.create(10, 20).set_right(5).right)
    5
    """
    yield Pair.create(l, r).set_left(new_l), Pair.create(new_l, r)
    yield Pair.create(l, r).set_right(new_r), Pair.create(l, new_r)


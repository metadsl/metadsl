from __future__ import annotations
import typing

from ..expressions import *
from ..matching import *
from .abstraction import *
from .rules import *

__all__ = ["Maybe"]
T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Maybe(Expression, typing.Generic[T]):
    """
    An optional value.
    """

    @expression
    @classmethod
    def nothing(cls) -> Maybe[T]:
        ...

    @expression
    @classmethod
    def just(cls, value: T) -> Maybe[T]:
        ...

    @expression
    def match(self, nothing: U, just: Abstraction[T, U]) -> U:
        ...


@rules.append
@rule
def maybe_match_nothing(nothing: U, just: Abstraction[T, U]) -> R[U]:
    return Maybe[T].nothing().match(nothing, just), lambda: nothing


@rules.append
@rule
def maybe_match_just(nothing: U, just: Abstraction[T, U], v: T):
    return Maybe.just(v).match(nothing, just), lambda: just(v)

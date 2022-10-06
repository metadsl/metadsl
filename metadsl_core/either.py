from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .conversion import *
from .maybe import *
from .strategies import *

__all__ = ["Either"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


class Either(Expression, typing.Generic[T, U], wrap_methods=True):
    @classmethod
    def left(cls, value: T) -> Either[T, U]:
        ...

    @classmethod
    def right(cls, value: U) -> Either[T, U]:
        ...

    def match(self, left: Abstraction[T, V], right: Abstraction[U, V]) -> V:
        ...


@register_core  # type: ignore
@rule
def either_match(l: Abstraction[T, V], r: Abstraction[U, V], t: T, u: U) -> R[V]:
    yield Either[T, U].left(t).match(l, r), lambda: l(t)  # type: ignore
    yield Either[T, U].right(u).match(l, r), lambda: r(u)  # type: ignore


@register_convert
@rule
def convert_to_either(x: object) -> R[Maybe[Either[T, U]]]:
    """
    Converting to an either should try converting to both types.
    If either matches, then that should be the result. If neither
    can be converted, then the result should be nothing.
    """

    convert_left = (
        Converter[T]  # type: ignore
        .convert(x)
        .map(Abstraction.from_fn(Either[T, U].left))
    )
    convert_right = Converter[U].convert(x).map(Abstraction.from_fn(Either[T, U].right))

    return (Converter[Either[T, U]].convert(x), convert_left | convert_right)

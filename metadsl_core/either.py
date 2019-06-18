from __future__ import annotations
import typing

from metadsl import *
from .conversion import *
from .maybe import *
from .abstraction import *
from .rules import *

__all__ = ["Either"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


class Either(Expression, typing.Generic[T, U]):
    @expression
    @classmethod
    def left(cls, value: T) -> Either[T, U]:
        ...

    @expression
    @classmethod
    def right(cls, value: U) -> Either[T, U]:
        ...

    @expression
    def match(self, left: Abstraction[T, V], right: Abstraction[U, V]) -> V:
        ...


@rules.append
@rule
def either_match_left(l: Abstraction[T, V], r: Abstraction[U, V], v: T) -> R[V]:
    return Either[T, U].left(v).match(l, r), lambda: l(v)


@rules.append
@rule
def either_match_right(l: Abstraction[T, V], r: Abstraction[U, V], v: U) -> R[V]:
    return Either[T, U].right(v).match(l, r), lambda: r(v)


@rules.append
@rule
def convert_to_either(x: object) -> R[Maybe[Either[T, U]]]:
    def replacement() -> Maybe[Either[T, U]]:
        convert_left: Maybe[T] = Converter[T].convert(x)
        convert_right: Maybe[U] = Converter[U].convert(x)

        no_conversion = Maybe[Either[T, U]].nothing()

        converted_left: Abstraction[T, Maybe[Either[T, U]]] = a(
            lambda v: Maybe.just(Either[T, U].left(v))
        )
        converted_right: Abstraction[U, Maybe[Either[T, U]]] = a(
            lambda v: Maybe.just(Either[T, U].right(v))
        )
        no_left_conversion: Maybe[Either[T, U]] = convert_right.match(
            no_conversion, converted_right
        )

        return convert_left.match(no_left_conversion, converted_left)

    return (Converter[Either[T, U]].convert(x), replacement)

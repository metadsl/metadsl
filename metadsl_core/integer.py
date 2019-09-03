from __future__ import annotations

from metadsl import *
from .conversion import *
from .rules import *
from .maybe import *
from .boolean import *

__all__ = ["Integer"]


class Integer(Expression):
    @expression
    @classmethod
    def from_int(cls, i: int) -> Integer:
        ...

    @expression
    def __add__(self, other: Integer) -> Integer:
        ...

    @expression
    def __sub__(self, other: Integer) -> Integer:
        ...

    @expression
    def __mul__(self, other: Integer) -> Integer:
        ...

    @expression
    def eq(self, other: Integer) -> Boolean:
        ...


@register
@rule
def integer_math(l: int, r: int) -> R[Integer]:
    yield Integer.from_int(l) + Integer.from_int(r), lambda: Integer.from_int(l + r)
    yield Integer.from_int(l) - Integer.from_int(r), lambda: Integer.from_int(l - r)
    yield Integer.from_int(l) * Integer.from_int(r), lambda: Integer.from_int(l * r)


@register
@rule
def integer_eq(l: int, r: int) -> R[Boolean]:
    return Integer.from_int(l).eq(Integer.from_int(r)), lambda: Boolean.create(l == r)


@register_convert
@rule
def convert_integer(i: int) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(i), lambda: Maybe.just(Integer.from_int(i))

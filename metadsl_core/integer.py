from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .boolean import *
from .conversion import *
from .maybe import *
from .strategies import *

__all__ = ["Integer"]

T = typing.TypeVar("T")


class Integer(Expression, wrap_methods=True):
    @classmethod
    def from_int(cls, i: int) -> Integer:
        ...

    def __add__(self, other: Integer) -> Integer:
        ...

    def __sub__(self, other: Integer) -> Integer:
        ...

    def __mul__(self, other: Integer) -> Integer:
        ...

    def __floordiv__(self, other: Integer) -> Integer:
        ...

    def __mod__(self, other: Integer) -> Integer:
        ...

    def eq(self, other: Integer) -> Boolean:
        ...

    def __lt__(self, other: Integer) -> Boolean:
        ...

    def __le__(self, other: Integer) -> Boolean:
        ...

    def __gt__(self, other: Integer) -> Boolean:
        ...

    def __ge__(self, other: Integer) -> Boolean:
        ...

    def fold(self, initial: T, fn: Abstraction[Integer, Abstraction[T, T]]) -> T:
        ...

    @classmethod
    def zero(cls) -> Integer:
        return Integer.from_int(0)

    @classmethod
    def one(cls) -> Integer:
        return cls.zero().inc

    @property
    def inc(self) -> Integer:
        return self + Integer.from_int(1)

    @classmethod
    def infinity(cls) -> Integer:
        ...


register_ds(default_rule(Integer.zero))
register_ds(default_rule(Integer.inc))
register_ds(default_rule(Integer.one))


@register_ds
@rule
def integer_math(l: int, r: int) -> R[Integer]:
    yield Integer.from_int(l) + Integer.from_int(r), lambda: Integer.from_int(l + r)
    yield Integer.from_int(l) - Integer.from_int(r), lambda: Integer.from_int(l - r)
    yield Integer.from_int(l) * Integer.from_int(r), lambda: Integer.from_int(l * r)
    yield Integer.from_int(l) // Integer.from_int(r), lambda: Integer.from_int(l // r)
    yield Integer.from_int(l) % Integer.from_int(r), lambda: Integer.from_int(l % r)

    inf = Integer.infinity()
    yield Integer.from_int(l) + inf, inf
    yield inf + Integer.from_int(r), inf


@register_ds
@rule
def integer_comparison(l: int, r: int) -> R[Boolean]:
    li = Integer.from_int(l)
    ri = Integer.from_int(r)
    yield li.eq(ri), lambda: Boolean.create(l == r)
    yield li < ri, lambda: Boolean.create(l < r)
    yield li <= ri, lambda: Boolean.create(l <= r)
    yield li > ri, lambda: Boolean.create(l > r)
    yield li >= ri, lambda: Boolean.create(l >= r)

    inf = Integer.infinity()
    true = Boolean.true()
    false = Boolean.false()

    yield li.eq(inf), false
    yield inf.eq(ri), false
    yield li < inf, true
    yield inf < ri, false
    yield li <= inf, true
    yield inf <= ri, false
    yield li > inf, false
    yield inf > ri, true
    yield li >= inf, false
    yield inf >= ri, true


@register_ds
@rule
def fold(i: int, initial: T, fn: Abstraction[Integer, Abstraction[T, T]]) -> R[T]:
    def inner() -> T:
        value = initial
        for i_ in range(i):
            value = fn(Integer.from_int(i_))(value)
        return value

    return Integer.from_int(i).fold(initial, fn), inner


@register_convert
@rule
def convert_integer(i: int) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(i), Maybe.just(Integer.from_int(i))

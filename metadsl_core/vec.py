from __future__ import annotations

import typing

from metadsl import *
from .integer import *
from .maybe import *
from .conversion import *
from .abstraction import *
from .pair import *
from .rules import *

T = typing.TypeVar("T")
U = typing.TypeVar("U")

__all__ = ["Vec"]


class Vec(Expression, typing.Generic[T]):
    """
    A tuple of homogonous types.
    """

    @expression
    def __getitem__(self, index: Integer) -> T:
        """
        >>> execute_core(Vec.create(10, 11)[Integer.from_int(1)])
        11
        """
        ...

    @expression
    @classmethod
    def create(cls, *items: T) -> Vec[T]:
        ...

    @expression
    def map(self, fn: Abstraction[T, U]) -> Vec[U]:
        ...

    @expression
    def append(self, x: T) -> Vec[T]:
        """
        >>> execute_core(Vec.create(10).append(11)) == Vec.create(10, 11)
        True
        """
        ...

    @expression
    def fold(self, initial: U, fn: Abstraction[U, Abstraction[T, U]]) -> U:
        """
        Like this:

            def fold(xs, initial, fn):
                ret = initial
                for x in xs:
                    ret = fn(ret)(x)
                return ret
        """


@register
@rule
def getitem(i: int, xs: typing.Sequence[T]) -> R[T]:
    return (Vec[T].create(*xs)[Integer.from_int(i)], lambda: xs[i])


@register
@rule
def map(fn: Abstraction[T, U], xs: typing.Sequence[T]) -> R[Vec[U]]:
    return (Vec[T].create(*xs).map(fn), lambda: Vec[U].create(*(fn(x) for x in xs)))


@register
@rule
def append(xs: typing.Sequence[T], x: T) -> R[Vec[T]]:
    return (Vec[T].create(*xs).append(x), lambda: Vec[T].create(*xs, x))


# def tuple_all(t: Vec[Maybe[T]]) -> Maybe[Vec[T]]:
#     # accumulate a maybe tuple of T, representng the partial list so far
#     @Abstraction.from_fn
#     def fn(tpl: Maybe[Vec[T]]) -> Abstraction[Maybe[T], Maybe[Vec[T]]]:
#         @Abstraction.from_fn
#         def inner(x: Maybe[T]) -> Maybe[Vec[T]]:
#             @Abstraction.from_fn
#             def tpl_matched(just_tpl: Vec[T]) -> Maybe[Vec[T]]:

#                 @Abstraction.from_fn
#                 def x_matched(just_x: T) -> Maybe[Vec[T]]:
#                     return just_tpl.append(just_x)

#                 return x.match(
#                     Maybe[Vec[T]].nothing(),
#                     x_matched
#                 )
#             return tpl.match(
#                 tpl,
#                 tpl_matched
#             )
#         return inner

#     return t.fold(Maybe.just(Vec[T].create()), fn)


@register
@rule
def convert_tuple(xs: object) -> R[Maybe[Vec[T]]]:
    def replacement() -> Maybe[Vec[T]]:
        res = Maybe.just(Vec[T].create())
        # Only convert tuples
        if not isinstance(xs, tuple):
            raise NoMatch
        for x in xs:  # type: ignore

            @Abstraction.from_fn
            def fn(b: Pair[Vec[T], T]) -> Vec[T]:
                return b.left().append(b.right())

            res = (res & Converter[T].convert(x)).map(fn)
        return res

    return Converter[Vec[T]].convert(xs), replacement


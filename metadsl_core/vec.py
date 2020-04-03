from __future__ import annotations

import typing

from metadsl import *
from .boolean import *
from .integer import *
from .maybe import *
from .conversion import *
from .abstraction import *
from .pair import *
from .rules import *

T = typing.TypeVar("T")
U = typing.TypeVar("U")

__all__ = ["Vec", "Selection"]


class NoValue(Expression, typing.Generic[T]):
    """
    Returned by a getitem function that can have no inputs
    """

    @expression
    @classmethod
    def create(cls) -> T:
        ...


class Selection(Expression):
    @expression
    @classmethod
    def create_slice(cls, start: Integer, stop: Integer, step: Integer) -> Selection:
        """
        Like a python slice, but no negatives. start <= i < stop where i % step == start
        """
        ...

    @expression
    @classmethod
    def create_slice_optional(
        cls, start: Maybe[Integer], stop: Maybe[Integer], step: Maybe[Integer]
    ) -> Selection:
        return cls.create_slice(
            start.default(Integer.zero()),
            stop.default(Integer.infinity()),
            step.default(Integer.one()),
        )

    @expression
    def __call__(self, idx: Integer) -> Boolean:
        """
        Returns whether an index is selected by an index.
        """
        ...

register(default_rule(Selection.create_slice_optional))

class Vec(Expression, typing.Generic[T]):
    """
    A tuple of homogonous types.
    """

    @expression
    def __getitem__(self, index: Integer) -> T:
        ...

    @expression
    def select(self, selection: Selection) -> Vec[T]:
        ...

    # @expression
    # def full_index

    # @expression
    # def full_single_index

    @expression
    @classmethod
    def create(cls, *items: T) -> Vec[T]:
        ...

    @expression
    def map(self, fn: Abstraction[T, U]) -> Vec[U]:
        ...

    @expression
    def append(self, x: T) -> Vec[T]:
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

    @expression
    def __add__(self, other: Vec[T]) -> Vec[T]:
        ...

    @expression  # type: ignore
    @property
    def length(self) -> Integer:
        ...

    @expression
    def take(self, i: Integer) -> Vec[T]:
        ...

    @expression
    def drop(self, i: Integer) -> Vec[T]:
        ...

    @expression
    @classmethod
    def create_fn(cls, length: Integer, fn: Abstraction[Integer, T]) -> Vec[T]:
        ...

    @expression
    @classmethod
    def lift_maybe(cls, vec: Vec[Maybe[T]]) -> Maybe[Vec[T]]:
        ...


@register
@rule
def create_fn_rules(
    l: Integer,
    fn: Abstraction[Integer, T],
    x: T,
    l1: Integer,
    fn1: Abstraction[Integer, T],
    n: Integer,
    s: Selection,
):
    v = Vec.create_fn(l, fn)
    v1 = Vec.create_fn(l1, fn1)
    one = Integer.from_int(1)
    yield v[l], fn(l)
    yield v.append(x), Vec.create_fn(
        l + one, Abstraction[Integer, T].from_fn(lambda i: (i < l).if_(fn(i), x))
    )
    yield v + v1, Vec.create_fn(
        l + l1,
        Abstraction[Integer, T].from_fn(lambda i: (i < l).if_(fn(i), fn1(i - l1))),
    )
    yield v.length, l
    yield v.take(n), Vec.create_fn(l - n, fn)
    yield v.drop(n), Vec.create_fn(
        l - n, Abstraction[Integer, T].from_fn(lambda i: fn(i + n)),
    )
    yield v.select(s), l.fold(
        Vec.create_fn(
            Integer.from_int(0),
            Abstraction[Integer, T].from_fn(lambda _: NoValue[T].create()),
        ),
        Abstraction[Integer, Abstraction[Vec[T], Vec[T]]].from_fn(
            lambda i: Abstraction[Vec[T], Vec[T]].from_fn(
                # if the selection is true for this index, then append the
                # value that was at the previous vec, otherwise keep it the same
                lambda new_v: s(i).if_(new_v.append(v[i]), new_v)
            )
        ),
    )


@register
@rule
def select_slice(
    start: Integer, stop: Integer, step: Integer, i: Integer
) -> R[Boolean]:
    return (
        Selection.create_slice(start, stop, step)(i),
        (start <= i).and_(i < stop).and_((i % step).eq(start)),
    )


@register  # type: ignore
@rule
def length_rule(xs: typing.Sequence[T]) -> R[Integer]:
    return (Vec[T].create(*xs).length, lambda: Integer.from_int(len(xs)))


@register  # type: ignore
@rule
def take_drop_rule(xs: typing.Sequence[T], i: int) -> R[Vec[T]]:
    yield (
        Vec[T].create(*xs).take(Integer.from_int(i)),
        lambda: Vec[T].create(*xs[:i]),
    )
    yield (
        Vec[T].create(*xs).drop(Integer.from_int(i)),
        lambda: Vec[T].create(*xs[i:]),
    )


@register  # type: ignore
@rule
def add_rule(ls: typing.Sequence[T], rs: typing.Sequence[T]) -> R[Vec[T]]:
    return (Vec[T].create(*ls) + Vec[T].create(*rs), Vec[T].create(*ls, *rs))


@register  # type: ignore
@rule
def getitem(i: int, xs: typing.Sequence[T]) -> R[T]:
    return (Vec[T].create(*xs)[Integer.from_int(i)], lambda: xs[i])


@register
@rule
def map(fn: Abstraction[T, U], xs: typing.Sequence[T]) -> R[Vec[U]]:
    return (
        Vec[T].create(*xs).map(fn),  # type: ignore
        lambda: (Vec.create(*(fn(x) for x in xs))) if xs else Vec[U].create(),
    )


@register
@rule
def append(xs: typing.Sequence[T], x: T) -> R[Vec[T]]:
    return (Vec[T].create(*xs).append(x), lambda: Vec.create(*xs, x))


@register
@rule
def vec_select(xs: typing.Sequence[T], s: Selection) -> R[Vec[T]]:
    def inner() -> Vec[T]:
        result = Vec[T].create()
        for i, x in enumerate(xs):
            included = s(Integer.from_int(i))
            #
            result = included.if_(result.append(x), result)
        return result

    return Vec[T].create(*xs).select(s), inner


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
def fold_vec(
    xs: typing.Sequence[T], initial: U, fn: Abstraction[U, Abstraction[T, U]]
) -> R[U]:
    def inner() -> U:
        res = initial
        for x in xs:
            res = fn(res)(x)
        return res

    return (Vec.create(*xs).fold(initial, fn), inner)


@register_convert
@rule
def convert_vec(xs: typing.Sequence[object]) -> R[Maybe[Vec[T]]]:
    def inner() -> Maybe[Vec[T]]:
        if not isinstance(xs, tuple):
            raise NoMatch
        return Vec[T].lift_maybe(
            Vec[Maybe[T]].create(*(Converter[T].convert(x) for x in xs))
        )

    return (
        Converter[Vec[T]].convert(xs),
        inner,
    )


@register_convert
@rule
def convert_slice(s: slice) -> R[Maybe[Selection]]:
    return (
        Converter[Selection].convert(s),
        lambda: (
            Converter[Maybe[Integer]].convert(s.start)
            & (
                Converter[Maybe[Integer]].convert(s.stop)
                & Converter[Maybe[Integer]].convert(s.step)
            )
        ).map(
            Abstraction[
                Pair[Maybe[Integer], Pair[Maybe[Integer], Maybe[Integer]]], Selection
            ].from_fn(
                lambda s_: Selection.create_slice_optional(
                    s_.left, s_.right.left, s_.right.right
                )
            )
        ),
    )


@register
@rule
def lift_maybe(v: Vec[Maybe[T]]) -> R[Maybe[Vec[T]]]:

    return (
        Vec.lift_maybe(v),
        v.fold(
            Maybe.just(Vec[T].create()),
            Abstraction[Maybe[Vec[T]], Abstraction[Maybe[T], Maybe[Vec[T]]]].from_fn(
                lambda xs: Abstraction[Maybe[T], Maybe[Vec[T]]].from_fn(
                    lambda x: (xs & x).map(
                        Abstraction[Pair[Vec[T], T], Vec[T]].from_fn(
                            lambda both: both.left.append(both.right)
                        )
                    )
                )
            ),
        ),
    )

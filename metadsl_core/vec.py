from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .boolean import *
from .integer import *
from .maybe import *
from .conversion import *
from .abstraction import *
from .pair import *
from .strategies import *

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
    """
    A selection represents a mapping from a vector to a new vector, that includes some subset of the old
    values, but in new positions. Old values can be duplicated.
    """

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
    @classmethod
    def create_indices(cls, indices: Vec[Integer]) -> Selection:
        """
        Selection indices from this vector.
        """
        ...

    @expression
    def old_to_new(self, idx: Integer) -> Vec[Integer]:
        """
        Map from old index to where it shows up in new vector.
        """
        ...

    @expression
    def new_to_old(self, idx: Integer) -> Integer:
        """
        Map from new index to the old index it came from.
        """
        ...

    @expression
    def length(self, old_length: Integer) -> Integer:
        """
        Length of new parts.
        """
        ...


register_ds(default_rule(Selection.create_slice_optional))


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

    @expression
    def set(self, i: Integer, value: T) -> Vec[T]:
        ...

    @expression
    def set_selection(self, s: Selection, values: Vec[T]) -> Vec[T]:
        ...

    @expression  # type: ignore
    @property
    def empty(self) -> Boolean:
        return self.length.eq(Integer.zero())

    @expression  # type: ignore
    @property
    def first(self) -> Maybe[T]:
        return self.empty.if_(Maybe[T].nothing(), Maybe.just(self[Integer.zero()]))


register_ds(default_rule(Vec[T].empty))
register_ds(default_rule(Vec[T].first))


@register_ds
@rule
def create_fn_rules(
    l: Integer,
    fn: Abstraction[Integer, T],
    x: T,
    l1: Integer,
    i: Integer,
    fn1: Abstraction[Integer, T],
    n: Integer,
    s: Selection,
):
    v = Vec.create_fn(l, fn)
    v1 = Vec.create_fn(l1, fn1)
    one = Integer.from_int(1)
    yield v[i], fn(i)
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
    yield v.select(s), Vec.create_fn(
        s.length(l), Abstraction[Integer, T].from_fn(lambda i: v[s.new_to_old(i)]),
    )
    yield v.set(n, x), Vec.create_fn(
        l, Abstraction[Integer, T].from_fn(lambda i: i.eq(n).if_(x, fn(i)))
    )
    # set selection maps each old index, looking up the first new one on the new v, if there
    # are any, otherwise, use old v
    yield v.set_selection(s, v1), Vec.create_fn(
        l,
        Abstraction[Integer, T].from_fn(
            lambda i: s.old_to_new(i).first.match(fn(i), fn1)
        ),
    )


@register_ds
@rule
def select_slice(start: Integer, stop: Integer, step: Integer, i: Integer):
    s = Selection.create_slice(start, stop, step)
    yield (
        s.old_to_new(i),
        # If the index is less than the stop index, and is on the step from the start,
        # return the new one, otherwise return none
        (i < stop)
        .and_((i % step).eq(start))
        .if_(Vec.create((i - start) // step), Vec[Integer].create()),
    )

    yield (s.new_to_old(i), start + (i * step))
    # Compute the actual stop if one is specified, by taking min of stop and old length "i"
    actual_stop = (i < stop).if_(i, stop)
    yield (s.length(i), (stop - actual_stop) // step)


@register_ds  # type: ignore
@rule
def length_rule(xs: typing.Sequence[T]) -> R[Integer]:
    return (Vec[T].create(*xs).length, lambda: Integer.from_int(len(xs)))


@register_ds  # type: ignore
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


@register_ds  # type: ignore
@rule
def add_rule(ls: typing.Sequence[T], rs: typing.Sequence[T]) -> R[Vec[T]]:
    return (Vec[T].create(*ls) + Vec[T].create(*rs), Vec[T].create(*ls, *rs))


@register_ds  # type: ignore
@rule
def getitem(i: int, xs: typing.Sequence[T]) -> R[T]:
    return (Vec[T].create(*xs)[Integer.from_int(i)], lambda: xs[i])


@register_ds
@rule
def map(fn: Abstraction[T, U], xs: typing.Sequence[T]) -> R[Vec[U]]:
    return (
        Vec[T].create(*xs).map(fn),  # type: ignore
        lambda: (Vec.create(*(fn(x) for x in xs))) if xs else Vec[U].create(),
    )


@register_ds
@rule
def append(xs: typing.Sequence[T], x: T) -> R[Vec[T]]:
    return (Vec[T].create(*xs).append(x), lambda: Vec.create(*xs, x))


# TODO: Replace with exact replacement for slice
@register_ds
@rule
def vec_select(xs: typing.Sequence[T], s: Selection) -> R[Vec[T]]:
    v = Vec[T].create(*xs)

    def inner() -> Vec[T]:
        # contains a list of of indices that we should lookup in the current vec
        result_idxs = Vec[Integer].create()
        for i in range(len(xs)):
            result_idxs += s.old_to_new(Integer.from_int(i))
        # naw just do a fold here, oh well!

        # TODO: Should this just be a Vector.from_fn instead?
        return result_idxs.fold(
            Vec[T].create(),
            Abstraction[Vec[T], Abstraction[Integer, Vec[T]]].from_fn(
                lambda result: Abstraction[Integer, Vec[T]].from_fn(
                    lambda i: result.append(v[i])
                )
            ),
        )

    return v.select(s), inner


@register_ds
@rule
def vec_set(xs: typing.Sequence[T], i: int, value: T) -> R[Vec[T]]:
    return (
        Vec[T].create(*xs).set(Integer.from_int(i), value),
        lambda: Vec[T].create(*(value if i == i_ else v for i_, v in enumerate(xs))),
    )


@register_ds
@rule
def vec_set_selection(
    xs: typing.Sequence[T], start: int, stop: int, step: int, values: typing.Sequence[T]
) -> R[Vec[T]]:
    def inner() -> Vec[T]:
        l = list(xs)
        l[start:stop:step] = list(values)
        return Vec[T].create(*l)

    yield (
        Vec[T]
        .create(*xs)
        .set_selection(
            Selection.create_slice(
                Integer.from_int(start), Integer.from_int(stop), Integer.from_int(step)
            ),
            Vec[T].create(*values),
        ),
        inner,
    )

    def inner_inf() -> Vec[T]:
        l = list(xs)
        l[start::step] = list(values)
        return Vec[T].create(*l)

    yield (
        Vec[T]
        .create(*xs)
        .set_selection(
            Selection.create_slice(
                Integer.from_int(start), Integer.infinity(), Integer.from_int(step)
            ),
            Vec[T].create(*values),
        ),
        inner,
    )


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


@register_ds
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


@register_core
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

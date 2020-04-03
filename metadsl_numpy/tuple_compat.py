from __future__ import annotations
import typing


from metadsl import *
from metadsl_core import *
from .bool_compat import *
from .injest import *
from .int_compat import *
from .boxing import *


__all__ = ["HomoTupleCompat"]


T = typing.TypeVar("T")
U = typing.TypeVar("U")


class HomoTupleCompat(Expression, typing.Generic[T, U]):
    """
    Should follow Python API for tuple with homogoneous types. 


    T is the outer type, when we are getting the item.
    U is the inner type of the items, that they will be stored as.

    """

    @expression
    @classmethod
    def from_maybe_vec(cls, v: Maybe[Vec[U]]) -> HomoTupleCompat[T, U]:
        ...

    @expression  # type: ignore
    @property
    def to_maybe_vec(self) -> Maybe[Vec[U]]:
        ...

    # TODO: allow multiple? how do we know if we are slicing or not?

    # Should the getitem return a union?

    # i.e. how does it know which one to use?
    @expression
    def __getitem__(self, idx: object) -> T:
        ...

    #     compat_tp, inner_tp = guess_type(idx)
    #     # If the idx
    #     if compat_tp == IntCompat

    @expression  # type: ignore
    @property
    def length(self) -> IntCompat:
        ...

    @expression
    def __add__(self, other: object) -> HomoTupleCompat[T, U]:
        ...

    @expression
    def __radd__(self, other: object) -> HomoTupleCompat[T, U]:
        ...


@guess.register(HomoTupleCompat)
def guess_homo_tuple(ht: HomoTupleCompat[T, U]) -> Guess[Vec[U], HomoTupleCompat[T, U]]:
    return ht.to_maybe_vec, ht.from_maybe_vec


@expression
def _homo_tuple_example(outer: T, inner: Maybe[U]) -> HomoTupleCompat[T, U]:
    ...


@guess.register
def guess_homo_tuple_tuple(b: tuple) -> Guess[Vec[T], HomoTupleCompat[object, T]]:
    maybes: typing.List[Maybe[T]]
    wrap: typing.Callable[[Maybe[T]], object]
    wrap, maybes = guess_all(*b)
    maybe_vec = Vec.lift_maybe(Vec.create(*maybes))

    # Create a homo tuple of the right type, so we can grab the `from_maybe_vec`
    # classmethod off of it
    inner_instance = maybes[0]
    outer_instance = wrap(inner_instance)
    ht = _homo_tuple_example(outer_instance, inner_instance)

    return maybe_vec, ht.from_maybe_vec


@register_convert
@rule
def to_from_maybe_vec(v: Maybe[Vec[U]]) -> R[Maybe[Vec[U]]]:
    return HomoTupleCompat[T, U].from_maybe_vec(v).to_maybe_vec, v


@register_convert
@rule
def convert_to_vec(v: Maybe[Vec[U]]) -> R[Maybe[Vec[U]]]:
    return Converter[Vec[T]].convert(HomoTupleCompat[T, U].from_maybe_vec(v)), v


@register_convert
@rule
def box_homo_tuple(v: Maybe[Vec[U]]) -> R[HomoTupleCompat[T, U]]:
    return (
        Boxer[HomoTupleCompat[T, U], Vec[U]].box(v),
        HomoTupleCompat[T, U].from_maybe_vec(v),
    )


@register_convert
@rule
def getitem(v: Maybe[Vec[U]], idx: object) -> R[T]:
    """
    Try to convert getitem to integer and index
    """
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v)[idx],
        Boxer[T, U].box(
            (v & Converter[Integer].convert(idx)).map(
                Abstraction[Pair[Vec[U], Integer], U].from_fn(
                    lambda xs: xs.left[xs.right]
                )
            )
        ),
    )


@register_convert
@rule
def length(v: Maybe[Vec[U]]) -> R[IntCompat]:
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v).length,
        IntCompat.from_maybe_integer(
            v.map(Abstraction[Vec[U], Integer].from_fn(lambda v: v.length))
        ),
    )


@register_convert
@rule
def add(v: Maybe[Vec[U]], o: object) -> R[HomoTupleCompat[T, U]]:
    both_converted = v & Converter[Vec[U]].convert(o)
    # add
    yield (
        HomoTupleCompat[T, U].from_maybe_vec(v) + o,
        HomoTupleCompat[T, U].from_maybe_vec(
            both_converted.map(
                Abstraction[Pair[Vec[U], Vec[U]], Vec[U]].from_fn(
                    lambda both: both.left + both.right
                )
            )
        ),
    )
    # radd
    yield (
        o + HomoTupleCompat[T, U].from_maybe_vec(v),
        HomoTupleCompat[T, U].from_maybe_vec(
            both_converted.map(
                Abstraction[Pair[Vec[U], Vec[U]], Vec[U]].from_fn(
                    lambda both: both.right + both.left
                )
            )
        ),
    )

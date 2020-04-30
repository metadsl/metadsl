from __future__ import annotations
import typing
import typing_inspect

from metadsl import *
from metadsl_core import *
from metadsl.typing_tools import get_type
from metadsl_rewrite import *

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

    def __getitem__(self, idx: object) -> typing.Union[T, HomoTupleCompat[T, U]]:
        """
        Don't use in strongly typed code.
        """
        # If we infer it to an int, then use the getitem int
        # otherwise use the slice
        try:
            injested_idx = injest(idx)
        except NotImplementedError:
            pass
        else:
            if isinstance(injested_idx, IntCompat):
                return self.getitem_int(idx)
        return self.getitem_slice(idx)

    # TODO: Rename to single and selection
    @expression
    def getitem_int(self, idx: object) -> T:
        ...

    @expression
    def getitem_slice(self, idx: object) -> HomoTupleCompat[T, U]:
        ...

    def __setitem__(self, idx: object, value: object) -> None:
        res = self.setitem(idx, value)

        self.function = res.function  # type: ignore
        self.args = res.args
        self.kwargs = res.kwargs

    @expression
    def setitem(self, idx: object, value: object) -> HomoTupleCompat[T, U]:
        ...

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


@guess_type.register(HomoTupleCompat)
def guess_homo_tuple(ht: HomoTupleCompat[T, U]):
    compat_tp, inner_tp = typing_inspect.get_args(get_type(ht))
    return get_type(ht), Vec[inner_tp]  # type: ignore


@guess_type.register(Vec)
def guess_homo_tuple_vec(b: Vec[T]):
    (arg_tp,) = typing_inspect.get_args(get_type(b))
    compat_tp, inner_tp = guess_type_of_type(arg_tp)
    return HomoTupleCompat[compat_tp, inner_tp], Vec[inner_tp]  # type: ignore


@guess_type.register
def guess_homo_tuple_tuple(b: tuple):
    compat_tp, inner_tp = guess_types(*b)
    return HomoTupleCompat[compat_tp, inner_tp], Vec[inner_tp]  # type: ignore


@register_convert
@rule
def to_from_maybe_vec(v: Maybe[Vec[U]]) -> R[Maybe[Vec[U]]]:
    return HomoTupleCompat[T, U].from_maybe_vec(v).to_maybe_vec, v


@register_convert
@rule
def convert_to_vec(v: Maybe[Vec[U]]) -> R[Maybe[Vec[U]]]:
    return Converter[Vec[U]].convert(HomoTupleCompat[T, U].from_maybe_vec(v)), v


@register_convert
@rule
def box_homo_tuple(v: Maybe[Vec[U]]) -> R[HomoTupleCompat[T, U]]:
    return (
        Boxer[HomoTupleCompat[T, U], Vec[U]].box(v),
        HomoTupleCompat[T, U].from_maybe_vec(v),
    )


@register_convert
@rule
def setitem(v: Maybe[Vec[U]], idx: object, value: object) -> R[HomoTupleCompat[T, U]]:
    """
    Convert setitem to eiter integer and single item, or selection and vector
    """
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v).setitem(idx, value),
        lambda: HomoTupleCompat[T, U].from_maybe_vec(
            (
                v
                & Converter[Either[Pair[Integer, U], Pair[Selection, Vec[U]]]].convert(
                    Pair.create(idx, value)
                )
            ).map(
                Abstraction[
                    Pair[Vec[U], Either[Pair[Integer, U], Pair[Selection, Vec[U]]]],
                    Vec[U],
                ].from_fn(
                    lambda xs: xs.right.match(
                        Abstraction[Pair[Integer, U], Vec[U]].from_fn(
                            lambda ys: xs.left.set(ys.left, ys.right)
                        ),
                        Abstraction[Pair[Selection, Vec[U]], Vec[U]].from_fn(
                            lambda ys: xs.left.set_selection(ys.left, ys.right)
                        ),
                    )
                )
            )
        ),
    )


@register_convert
@rule
def getitem_int(v: Maybe[Vec[U]], idx: object) -> R[T]:
    """
    Try to convert getitem to integer and index
    """
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v).getitem_int(idx),
        lambda: Boxer[T, U].box(
            (v & Converter[Integer].convert(idx)).map(
                Abstraction[Pair[Vec[U], Integer], U].from_fn(
                    lambda xs: xs.left[xs.right]
                )
            )
        ),
    )


@register_convert
@rule
def getitem_slice(v: Maybe[Vec[U]], idx: object) -> R[HomoTupleCompat[T, U]]:
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v).getitem_slice(idx),
        lambda: HomoTupleCompat[T, U].from_maybe_vec(
            (v & Converter[Selection].convert(idx)).map(
                Abstraction[Pair[Vec[U], Selection], Vec[U]].from_fn(
                    lambda xs: xs.left.select(xs.right)
                )
            )
        ),
    )


@register_convert
@rule
def length(v: Maybe[Vec[U]]) -> R[IntCompat]:
    return (
        HomoTupleCompat[T, U].from_maybe_vec(v).length,
        lambda: IntCompat.from_maybe_integer(
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
        lambda: HomoTupleCompat[T, U].from_maybe_vec(
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
        lambda: HomoTupleCompat[T, U].from_maybe_vec(
            both_converted.map(
                Abstraction[Pair[Vec[U], Vec[U]], Vec[U]].from_fn(
                    lambda both: both.right + both.left
                )
            )
        ),
    )

from __future__ import annotations

import numpy
from metadsl import *

from .vec import *
from .integer import *
from .conversion import *
from .rules import *
from .maybe import *
from .abstraction import *
from .pair import *
from .either import *


__all__ = ["arange", "IndxType", "NDArray"]


class IntCompat(Expression):
    """
    API should be work like Python's `int` type.
    """

    @expression
    def __add__(self, other: object) -> IntCompat:
        return IntCompat.from_maybe_integer(
            (Converter[Integer].convert(self) & Converter[Integer].convert(other)).map(
                Abstraction[Pair[Integer, Integer], Integer].from_fn(
                    lambda p: p.left + p.right
                )
            )
        )

    @expression
    @classmethod
    def from_maybe_integer(cls, i: Maybe[Integer]) -> IntCompat:
        ...


register_convert(default_rule(IntCompat.__add__))


@register_convert
@rule
def convert_to_integer(i: Maybe[Integer]) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(IntCompat.from_maybe_integer(i)), i


class TupleIntCompat(Expression):
    @expression
    def __getitem__(self, i: object) -> IntCompat:
        return IntCompat.from_maybe_integer(
            (Converter[Vec[Integer]].convert(self) & Converter[Integer].convert(i)).map(
                Abstraction[Pair[Vec[Integer], Integer], Integer].from_fn(
                    lambda p: p.left[p.right]
                )
            )
        )

    @expression
    @classmethod
    def from_vec_integer(cls, i: Maybe[Vec[Integer]]) -> TupleIntCompat:
        ...


register_convert(default_rule(TupleIntCompat.__getitem__))


@register_convert
@rule
def convert_to_vec_integer(i: Maybe[Vec[Integer]]) -> R[Maybe[Vec[Integer]]]:
    return Converter[Vec[Integer]].convert(TupleIntCompat.from_vec_integer(i)), i


IndxType = Either[Integer, Vec[Integer]]


class NDArray(Expression):
    @expression
    def __getitem__(self, idxs: IndxType) -> NDArray:
        ...

    @expression
    def __add__(self, other: NDArray) -> NDArray:
        ...

    @expression
    def to_ndarray(self) -> numpy.ndarray:
        ...

    @expression
    @classmethod
    def from_ndarray(self, n: numpy.ndarray) -> NDArray:
        ...


@register_unbox
@rule
def box_unbox_ndarray(n: numpy.ndarray) -> R[numpy.ndarray]:
    return NDArray.from_ndarray(n).to_ndarray(), n


class NDArrayCompat(Expression):
    @expression
    def __getitem__(self, idxs: object) -> NDArrayCompat:
        return NDArrayCompat.from_ndarray(
            (
                Converter[NDArray].convert(self)
                & Converter[Either[Integer, Vec[Integer]]].convert(idxs)
            ).map(
                Abstraction[
                    Pair[NDArray, Either[Integer, Vec[Integer]]], NDArray
                ].from_fn(lambda p: p.left[p.right])
            )
        )

    @expression
    def __add__(self, other: NDArrayCompat) -> NDArrayCompat:
        ...

    @expression
    @classmethod
    def from_ndarray(cls, n: Maybe[NDArray]) -> NDArrayCompat:
        ...

    @expression
    def to_ndarray(self) -> numpy.ndarray:
        ...


@register_unbox
@rule
def box_unbox_ndarray_compat(n: NDArray) -> R[numpy.ndarray]:
    return (NDArrayCompat.from_ndarray(Maybe.just(n)).to_ndarray(), n.to_ndarray())


@register_convert
@rule
def add_compat(l: NDArray, r: NDArray) -> R[NDArrayCompat]:
    return (
        NDArrayCompat.from_ndarray(Maybe.just(l))
        + NDArrayCompat.from_ndarray(Maybe.just(r)),
        NDArrayCompat.from_ndarray(Maybe.just(l + r)),
    )


register_convert(default_rule(NDArrayCompat.__getitem__))


@register_convert
@rule
def convert_to_ndarray(i: Maybe[NDArray]) -> R[Maybe[NDArray]]:
    return Converter[NDArray].convert(NDArrayCompat.from_ndarray(i)), i


@expression
def arange(stop: object) -> NDArrayCompat:
    return NDArrayCompat.from_ndarray(
        Converter[Integer].convert(stop).map(Abstraction.from_fn(arange_))
    )


register_convert(default_rule(arange))


@expression
def arange_(stop: Integer) -> NDArray:
    ...

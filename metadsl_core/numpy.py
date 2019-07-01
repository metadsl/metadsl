from __future__ import annotations

from metadsl import *

from .vec import *
from .integer import *
from .conversion import *
from .rules import *
from .maybe import *
from .abstraction import *
from .pair import *
from .either import *

__all__ = ["arange"]


class IntCompat(Expression):
    """
    API should be work like Python's `int` type.
    """

    @expression
    def __add__(self, other: object) -> IntCompat:
        return IntCompat.from_maybe_integer(
            (Converter[Integer].convert(self) & Converter[Integer].convert(other)).map(
                Abstraction[Pair[Integer, Integer], Integer].from_fn(
                    lambda p: p.left() + p.right()
                )
            )
        )

    @expression
    @classmethod
    def from_maybe_integer(cls, i: Maybe[Integer]) -> IntCompat:
        ...


register(default_rule(IntCompat.__add__))


@register
@rule
def convert_to_integer(i: Maybe[Integer]) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(IntCompat.from_maybe_integer(i)), i


class TupleIntCompat(Expression):
    @expression
    def __getitem__(self, i: object) -> IntCompat:
        return IntCompat.from_maybe_integer(
            (Converter[Vec[Integer]].convert(self) & Converter[Integer].convert(i)).map(
                Abstraction[Pair[Vec[Integer], Integer], Integer].from_fn(
                    lambda p: p.left()[p.right()]
                )
            )
        )

    @expression
    @classmethod
    def from_vec_integer(cls, i: Maybe[Vec[Integer]]) -> TupleIntCompat:
        ...


register(default_rule(TupleIntCompat.__getitem__))


@register
@rule
def convert_to_vec_integer(i: Maybe[Vec[Integer]]) -> R[Maybe[Vec[Integer]]]:
    return Converter[Vec[Integer]].convert(TupleIntCompat.from_vec_integer(i)), i


class NDArray(Expression):
    @expression
    def __getitem__(self, idxs: Either[Integer, Vec[Integer]]) -> NDArray:
        ...


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
                ].from_fn(lambda p: p.left()[p.right()])
            )
        )

    @expression
    @classmethod
    def from_ndarray(cls, n: Maybe[NDArray]) -> NDArrayCompat:
        ...


register(default_rule(NDArrayCompat.__getitem__))


@register
@rule
def convert_to_ndarray(i: Maybe[NDArray]) -> R[Maybe[NDArray]]:
    return Converter[NDArray].convert(NDArrayCompat.from_ndarray(i)), i


@expression
def arange(stop: object) -> NDArrayCompat:
    return NDArrayCompat.from_ndarray(
        Converter[Integer].convert(stop).map(Abstraction.from_fn(arange_))
    )


register(default_rule(arange))


@expression
def arange_(stop: Integer) -> NDArray:
    ...

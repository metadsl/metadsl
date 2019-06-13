"""
Useful for to convert object to boxed types.
"""
from __future__ import annotations
import typing

from .expressions import *
from .matching import *

__all__ = ["Converter", "convert_identity_rule", "convert_to_maybe", "Maybe"]
T = typing.TypeVar("T")


class Maybe(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def just(cls, value: T) -> Maybe[T]:
        ...

    @expression
    @classmethod
    def nothing(cls) -> Maybe[T]:
        ...


class Converter(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def convert(cls, value: object) -> Maybe[T]:
        """
        Converts a value to a certain type.
        """
        ...


@rule
def convert_identity_rule(value: T) -> R[Maybe[T]]:
    """
    When the value is an instance of the type being converted, we can convert it.
    """
    return Converter[T].convert(value), lambda: Maybe.just(value)


@rule
def convert_to_maybe(x: object) -> R[Maybe[Maybe[T]]]:
    return (
        Converter[Maybe[T]].convert(x),
        lambda: Maybe.just(
            Maybe[T].nothing() if x is None else Converter[T].convert(x)
        ),
    )

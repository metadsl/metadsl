"""
Useful for to convert object to boxed types.
"""
from __future__ import annotations
import typing

from metadsl import *
from .maybe import *
from .rules import *

__all__ = ["Converter", "convert_identity_rule", "convert_to_maybe"]
T = typing.TypeVar("T")


class Converter(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def convert(cls, value: object) -> Maybe[T]:
        """
        Converts a value to a certain type.
        """
        ...


@register_convert
@rule
def convert_identity_rule(value: T) -> R[Maybe[T]]:
    """
    When the value is an instance of the type being converted, we can convert it.
    """
    yield Converter[T].convert(value), Maybe.just(value)
    yield Converter[T].convert(Maybe.just(value)), Maybe.just(value)
    yield Converter[T].convert(Maybe[T].nothing()), Maybe[T].nothing()


@register_convert
@rule
def convert_to_maybe(x: object) -> R[Maybe[Maybe[T]]]:
    return (
        Converter[Maybe[T]].convert(x),
        lambda: Maybe.just(
            Maybe[T].nothing() if x is None else Converter[T].convert(x)
        ),
    )

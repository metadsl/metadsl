from __future__ import annotations
import typing

from metadsl import *
from metadsl_core import *
from metadsl_rewrite import *

__all__ = ["Boxer"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Boxer(Expression, typing.Generic[T, U]):
    """
    Box a value into the compat type T from type U.
    """

    @expression
    @classmethod
    def box(cls, value: Maybe[U]) -> T:
        ...

    @expression
    @classmethod
    def convert(cls, value: object) -> Maybe[U]:
        return Converter[U].convert(value)

    @expression
    @classmethod
    def convert_and_box(cls, value: object) -> T:
        return cls.box(cls.convert(value))


register_convert(default_rule(Boxer[T, U].convert))
register_convert(default_rule(Boxer[T, U].convert_and_box))

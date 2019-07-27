from __future__ import annotations

from metadsl import *
from .conversion import *
from .rules import *
from .maybe import *

__all__ = ["Integer"]


class Integer(Expression):
    @expression
    @classmethod
    def from_int(cls, i: int) -> Integer:
        ...

    @expression
    def __add__(self, other: Integer) -> Integer:
        ...

    @expression
    def __mul__(self, other: Integer) -> Integer:
        ...


@register_convert
@rule
def convert_integer(i: int) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(i), lambda: Maybe.just(Integer.from_int(i))

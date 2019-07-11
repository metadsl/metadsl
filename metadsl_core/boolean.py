from __future__ import annotations


from metadsl import *
from .rules import *
from .conversion import *
from .maybe import *


__all__ = ["Boolean"]


class Boolean(Expression):
    @expression
    @classmethod
    def create(cls, b: bool) -> Boolean:
        ...


@register
@rule
def convert_bool(b: bool) -> R[Maybe[Boolean]]:
    """
    >>> execute_rule(convert_bool, Converter[Boolean].convert(True)) ==  Maybe.just(Boolean.create(True))
    True
    >>> list(convert_bool(Converter[Boolean].convert("not bool")))
    []
    """
    return Converter[Boolean].convert(b), Maybe.just(Boolean.create(b))

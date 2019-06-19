from __future__ import annotations


from metadsl import *
from .rules import *
from .conversion import *
from .maybe import *


class Boolean(Expression):
    @expression
    @classmethod
    def create(cls, b: bool) -> Boolean:
        ...


@rules.append
@rule
def convert_bool(b: bool) -> R[Maybe[Boolean]]:
    """
    >>> execute_rule(convert_bool, Converter[Boolean].convert(True)) ==  Maybe.just(Boolean.create(True))
    True
    >>> list(convert_bool(Converter[Boolean].convert("not bool")))
    []
    """
    return Converter[Boolean].convert(b), lambda: Maybe.just(Boolean.create(b))

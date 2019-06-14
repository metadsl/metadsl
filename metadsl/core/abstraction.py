from __future__ import annotations
import dataclasses

from ..expressions import *
from ..matching import *
from .rules import *
import typing

__all__ = ["Abstraction"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


@dataclasses.dataclass(eq=False)
class Variable:
    """
    should only be equal to itself
    """

    def __str__(self):
        return str(id(self))

    def __repr__(self):
        return f"Variable({str(self)})"


class Abstraction(Expression, typing.Generic[T, U]):
    @expression
    def __call__(self, arg: T) -> U:
        ...

    @expression
    @classmethod
    def create(cls, var: T, body: U) -> Abstraction[T, U]:
        ...

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T], U]) -> Abstraction[T, U]:
        v: T = cls.create_variable(Variable())
        return cls.create(v, fn(v))

    @expression
    @classmethod
    def create_variable(cls, variable: Variable) -> T:
        ...


rules.append(default_rule(Abstraction.from_fn))


@rules.append
@rule
def beta_reduce(var: T, body: U, arg: T) -> R[U]:
    return (
        Abstraction[T, U].create(var, body)(arg),
        lambda: ExpressionReplacer({var: arg})(body),
    )

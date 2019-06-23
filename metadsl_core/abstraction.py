from __future__ import annotations

import dataclasses
import typing

from metadsl import *

from .rules import *

__all__ = ["Abstraction"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


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

    @expression
    def __add__(self, other: Abstraction[U, V]) -> Abstraction[T, V]:
        """
        Composes this function with another
        """
        ...


register(default_rule(Abstraction.from_fn))


@register
@rule
def compose(
    a: typing.Callable[[T], U], b: typing.Callable[[U], V]
) -> R[Abstraction[T, V]]:
    return (
        Abstraction.from_fn(a) + Abstraction.from_fn(b),
        lambda: Abstraction[T, V].from_fn(lambda v: b(a(v))),
    )


@register
@rule
def beta_reduce(var: T, body: U, arg: T) -> R[U]:
    return (
        Abstraction[T, U].create(var, body)(arg),
        lambda: ExpressionReplacer(UnhashableMapping(Item(var, arg)))(body),
    )

from __future__ import annotations

import dataclasses
import typing

from metadsl import *

from .rules import *

__all__ = ["Abstraction", "Variable"]

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
    def __add__(self, other: Abstraction[V, T]) -> Abstraction[V, U]:
        """
        Composes this function with another.
        (f + g)(x) == f(g(x))
        """
        ...

    @staticmethod
    @expression
    def fix(fn: Abstraction[T, T]) -> T:
        """
        Fixed pointer operator, used to define recursive functions.
        """
        return fn(Abstraction.fix(fn))


from_fn_rule = register(default_rule(Abstraction[T, U].from_fn))
fix_rule = register_post(default_rule(Abstraction.fix))


def _replace(body: U, var: T, arg: T) -> U:
    return ExpressionReplacer(UnhashableMapping(Item(var, arg)))(body)


@register
@rule
def compose(vl: T, bl: U, vr: V, br: T) -> R[Abstraction[V, U]]:
    # We want to define composition for the lambda calculus
    # We start with our two functions, each with a variable and a body:
    # f = 𝜆vl.bl
    # g = 𝜆vr.br
    # We want to compute their composition:
    # 𝜆x.f(g(x))
    # We can start by replacing function application with replacing all instances of the variable in the body
    # == f(br[vr/x])
    # == bl[vl/br[vr/x]]
    # Now, what we want is to pull out the `x` replacement to the outside, so we can create another function from this
    # Assuming no overlapping variables names in the scope, we should be able to do the replacements in sequence:
    # == bl[vl/br][vr/x]
    # == 𝜆vr.bl[vl/br]
    # this checks out typing wise, which is nice!

    return (
        Abstraction[T, U].create(vl, bl)  # type: ignore
        + Abstraction[V, T].create(vr, br),
        lambda: Abstraction.create(vr, _replace(bl, vl, br)),
    )


@register  # type: ignore
@rule
def beta_reduce(var: T, body: U, arg: T) -> R[U]:
    return (Abstraction[T, U].create(var, body)(arg), lambda: _replace(body, var, arg))

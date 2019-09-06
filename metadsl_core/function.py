"""
This module is built on top of the abstraction

It adds the ability to have multiple arities and names attached to functions.

Because MyPy doesn't support multiple arity generics, we need a seperate class for each arity of
function.
"""
from __future__ import annotations


from metadsl import *
from .rules import *
from .abstraction import *
import typing

__all__ = ["FunctionZero", "FunctionOne", "FunctionTwo", "FunctionThree"]
T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


class FunctionZero(Expression, typing.Generic[T]):
    """
    Function with zero args.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[], T]) -> FunctionZero[T]:
        return cls.create(fn.__name__, fn())

    @expression
    def __call__(self) -> T:
        ...

    @expression
    @classmethod
    def create(cls, name: str, val: T) -> FunctionZero[T]:
        ...


class FunctionOne(Expression, typing.Generic[T, U]):
    """
    Function with one arg.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T], U]) -> FunctionOne[T, U]:
        return cls.create(fn.__name__, Abstraction.from_fn(fn))

    @expression
    @classmethod
    def from_fn_recursive(
        cls, fn: typing.Callable[[FunctionOne[T, U], T], U]
    ) -> FunctionOne[T, U]:
        def inner(inner_abst: Abstraction[T, U]) -> Abstraction[T, U]:
            inner_fn = cls.create(fn.__name__, inner_abst)

            def inner_inner(arg1: T) -> U:
                return fn(inner_fn, arg1)

            return Abstraction[T, U].from_fn(inner_inner)

        return cls.create(
            fn.__name__,
            Abstraction.fix(
                Abstraction[Abstraction[T, U], Abstraction[T, U]].from_fn(inner)
            ),
        )

    @expression
    def __call__(self, arg: T) -> U:
        ...

    @expression
    @classmethod
    def create(cls, name: str, val: Abstraction[T, U]) -> FunctionOne[T, U]:
        ...


class FunctionTwo(Expression, typing.Generic[T, U, V]):
    """
    Function with two args.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T, U], V]) -> FunctionTwo[T, U, V]:
        @Abstraction.from_fn
        def inner(arg1: T) -> Abstraction[U, V]:
            @Abstraction.from_fn
            def inner_inner(arg2: U) -> V:
                return fn(arg1, arg2)

            return inner_inner

        return cls.create(fn.__name__, inner)

    @expression
    def __call__(self, arg1: T, arg2: U) -> V:
        ...

    @expression
    @classmethod
    def create(
        cls, name: str, val: Abstraction[T, Abstraction[U, V]]
    ) -> FunctionTwo[T, U, V]:
        ...


class FunctionThree(Expression, typing.Generic[T, U, V, X]):
    """
    Function with three args.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T, U, V], X]) -> FunctionThree[T, U, V, X]:
        @Abstraction.from_fn
        def inner(arg1: T) -> Abstraction[U, Abstraction[V, X]]:
            @Abstraction.from_fn
            def inner_inner(arg2: U) -> Abstraction[V, X]:
                @Abstraction.from_fn
                def inner_inner_inner(arg3: V) -> X:
                    return fn(arg1, arg2, arg3)

                return inner_inner_inner

            return inner_inner

        return cls.create(fn.__name__, inner)

    @expression
    def __call__(self, arg1: T, arg2: U, arg3: V) -> X:
        ...

    @expression
    @classmethod
    def create(
        cls, name: str, val: Abstraction[T, Abstraction[U, Abstraction[V, X]]]
    ) -> FunctionThree[T, U, V, X]:
        ...


register(default_rule(FunctionZero[T].from_fn))
register(default_rule(FunctionOne[T, U].from_fn))
register(default_rule(FunctionTwo[T, U, V].from_fn))
register(default_rule(FunctionThree[T, U, V, X].from_fn))

register(default_rule(FunctionOne[T, U].from_fn_recursive))


@register  # type: ignore
@rule
def zero_call(_: str, t: T) -> R[T]:
    return FunctionZero.create(_, t)(), t


@register  # type: ignore
@rule
def one_call(_: str, abst: Abstraction[T, U], t: T) -> R[U]:
    return FunctionOne.create(_, abst)(t), abst(t)


@register  # type: ignore
@rule
def two_call(_: str, abst: Abstraction[T, Abstraction[U, V]], t: T, u: U) -> R[V]:
    return FunctionTwo.create(_, abst)(t, u), abst(t)(u)


@register  # type: ignore
@rule
def three_call(
    _: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]], t: T, u: U, v: V
) -> R[X]:
    return FunctionThree.create(_, abst)(t, u, v), abst(t)(u)(v)

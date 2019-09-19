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
    def to_fn(self) -> typing.Callable[[], T]:
        ...

    @expression
    def __call__(self) -> T:
        ...

    @expression
    @classmethod
    def create(cls, name: str, val: T) -> FunctionZero[T]:
        ...

    @expression
    def value(self) -> T:
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
    def to_fn(self) -> typing.Callable[[T], U]:
        ...

    @expression
    @classmethod
    def from_fn_recursive(
        cls, fn: typing.Callable[[FunctionOne[T, U], T], U]
    ) -> FunctionOne[T, U]:
        @Abstraction.fix
        @Abstraction.from_fn
        def inner(inner_abst: Abstraction[T, U]) -> Abstraction[T, U]:
            inner_fn = cls.create(fn.__name__, inner_abst)

            @Abstraction.from_fn
            def inner_inner(arg1: T) -> U:
                return fn(inner_fn, arg1)

            return inner_inner

        return cls.create(fn.__name__, inner)

    @expression
    def __call__(self, arg: T) -> U:
        ...

    @expression
    @classmethod
    def create(cls, name: str, val: Abstraction[T, U]) -> FunctionOne[T, U]:
        ...

    @expression
    def abstraction(self) -> Abstraction[T, U]:
        ...


class FunctionTwo(Expression, typing.Generic[T, U, V]):
    """
    Function with two args.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T, U], V]) -> FunctionTwo[T, U, V]:
        def inner(arg1: T) -> Abstraction[U, V]:
            def inner_inner(arg2: U) -> V:
                return fn(arg1, arg2)

            return Abstraction.from_fn(inner_inner)

        return cls.create(fn.__name__, Abstraction.from_fn(inner))

    @expression
    def to_fn(self) -> typing.Callable[[T, U], V]:
        ...

    @expression
    @classmethod
    def from_fn_recursive(
        cls, fn: typing.Callable[[FunctionTwo[T, U, V], T, U], V]
    ) -> FunctionTwo[T, U, V]:
        @Abstraction.fix
        @Abstraction.from_fn
        def inner(
            inner_abst: Abstraction[T, Abstraction[U, V]]
        ) -> Abstraction[T, Abstraction[U, V]]:
            inner_fn = cls.create(fn.__name__, inner_abst)

            @Abstraction.from_fn
            def inner_inner(arg1: T) -> Abstraction[U, V]:
                @Abstraction.from_fn
                def inner_inner_inner(arg2: U) -> V:
                    return fn(inner_fn, arg1, arg2)

                return inner_inner_inner

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

    @expression
    def abstraction(self) -> Abstraction[T, Abstraction[U, V]]:
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
    def to_fn(self) -> typing.Callable[[T, U, V], X]:
        ...

    @expression
    @classmethod
    def from_fn_recursive(
        cls, fn: typing.Callable[[FunctionThree[T, U, V, X], T, U, V], X]
    ) -> FunctionThree[T, U, V, X]:
        @Abstraction.fix
        @Abstraction.from_fn
        def inner(
            inner_abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]
        ) -> Abstraction[T, Abstraction[U, Abstraction[V, X]]]:
            inner_fn = cls.create(fn.__name__, inner_abst)

            @Abstraction.from_fn
            def inner_inner(arg1: T) -> Abstraction[U, Abstraction[V, X]]:
                @Abstraction.from_fn
                def inner_inner_inner(arg2: U) -> Abstraction[V, X]:
                    @Abstraction.from_fn
                    def inner_inner_inner_inner(arg3: V) -> X:
                        return fn(inner_fn, arg1, arg2, arg3)

                    return inner_inner_inner_inner

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

    @expression
    def abstraction(self) -> Abstraction[T, Abstraction[U, Abstraction[V, X]]]:
        ...


register_pre(default_rule(FunctionZero[T].from_fn))
register_pre(default_rule(FunctionOne[T, U].from_fn))
register_pre(default_rule(FunctionTwo[T, U, V].from_fn))
register_pre(default_rule(FunctionThree[T, U, V, X].from_fn))

register_pre(default_rule(FunctionOne[T, U].from_fn_recursive))
register_pre(default_rule(FunctionTwo[T, U, V].from_fn_recursive))
register_pre(default_rule(FunctionThree[T, U, V, X].from_fn_recursive))


@register  # type: ignore
@rule
def zero_call(fn: FunctionZero[T]) -> R[T]:
    return fn(), fn.value()


@register  # type: ignore
@rule
def one_call(fn: FunctionOne[T, U], t: T) -> R[U]:
    return fn(t), fn.abstraction()(t)


@register  # type: ignore
@rule
def two_call(fn: FunctionTwo[T, U, V], t: T, u: U) -> R[V]:
    return fn(t, u), fn.abstraction()(t)(u)


@register  # type: ignore
@rule
def three_call(fn: FunctionThree[T, U, V, X], t: T, u: U, v: V) -> R[X]:
    return fn(t, u, v), fn.abstraction()(t)(u)(v)


@register  # type: ignore
@rule
def zero_value(_: str, t: T) -> R[T]:
    return FunctionZero.create(_, t).value(), t


@register  # type: ignore
@rule
def one_abstraction(_: str, abst: Abstraction[T, U]) -> R[Abstraction[T, U]]:
    return FunctionOne.create(_, abst).abstraction(), abst


@register  # type: ignore
@rule
def two_abstraction(
    _: str, abst: Abstraction[T, Abstraction[U, V]]
) -> R[Abstraction[T, Abstraction[U, V]]]:
    return FunctionTwo.create(_, abst).abstraction(), abst


@register  # type: ignore
@rule
def three_abstraction(
    _: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]
) -> R[Abstraction[T, Abstraction[U, Abstraction[V, X]]]]:
    return FunctionThree.create(_, abst).abstraction(), abst

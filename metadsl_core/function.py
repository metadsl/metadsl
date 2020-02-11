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

    @property  # type: ignore
    @expression
    def value(self) -> T:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
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
        @Abstraction.fix
        @Abstraction.from_fn
        def inner(inner_abst: Abstraction[T, U]) -> Abstraction[T, U]:
            inner_fn = cls.create(fn.__name__, inner_abst)

            @Abstraction.from_fn
            def inner(arg1: T) -> U:
                return fn(inner_fn, arg1)

            return inner

        return cls.create(fn.__name__, inner)

    @expression
    def __call__(self, arg: T) -> U:
        ...

    @expression
    @classmethod
    def create(cls, name: str, val: Abstraction[T, U]) -> FunctionOne[T, U]:
        ...

    @expression  # type: ignore
    @property
    def abstraction(self) -> Abstraction[T, U]:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
        ...

    @expression  # type: ignore
    @property
    def unfix(self) -> Abstraction[FunctionOne[T, U], FunctionOne[T, U]]:
        ...


class FunctionTwo(Expression, typing.Generic[T, U, V]):
    """
    Function with two args.
    """

    @expression
    @classmethod
    def from_fn(cls, fn: typing.Callable[[T, U], V]) -> FunctionTwo[T, U, V]:
        def inner(arg1: T) -> Abstraction[U, V]:
            def inner(arg2: U) -> V:
                return fn(arg1, arg2)

            return Abstraction.from_fn(inner)

        return cls.create(fn.__name__, Abstraction.from_fn(inner))

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
            def inner(arg1: T) -> Abstraction[U, V]:
                @Abstraction.from_fn
                def inner(arg2: U) -> V:
                    return fn(inner_fn, arg1, arg2)

                return inner

            return inner

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

    @expression  # type: ignore
    @property
    def abstraction(self) -> Abstraction[T, Abstraction[U, V]]:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
        ...

    @expression  # type: ignore
    @property
    def unfix(self) -> Abstraction[FunctionTwo[T, U, V], FunctionTwo[T, U, V]]:
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
            def inner(arg2: U) -> Abstraction[V, X]:
                @Abstraction.from_fn
                def inner(arg3: V) -> X:
                    return fn(arg1, arg2, arg3)

                return inner

            return inner

        return cls.create(fn.__name__, inner)

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
            def inner(arg1: T) -> Abstraction[U, Abstraction[V, X]]:
                @Abstraction.from_fn
                def inner(arg2: U) -> Abstraction[V, X]:
                    @Abstraction.from_fn
                    def inner(arg3: V) -> X:
                        return fn(inner_fn, arg1, arg2, arg3)

                    return inner

                return inner

            return inner

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

    @expression  # type: ignore
    @property
    def abstraction(self) -> Abstraction[T, Abstraction[U, Abstraction[V, X]]]:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
        ...

    @expression  # type: ignore
    @property
    def unfix(
        self,
    ) -> Abstraction[FunctionThree[T, U, V, X], FunctionThree[T, U, V, X]]:
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
def zero_call(_: str, v: T) -> R[T]:
    return FunctionZero.create(_, v)(), v


@register  # type: ignore
@rule
def one_call(_: str, a: Abstraction[T, U], t: T) -> R[U]:
    return FunctionOne.create(_, a)(t), a(t)


@register  # type: ignore
@rule
def two_call(_: str, a: Abstraction[T, Abstraction[U, V]], t: T, u: U) -> R[V]:
    return FunctionTwo.create(_, a)(t, u), a(t)(u)


@register  # type: ignore
@rule
def three_call(
    _: str, a: Abstraction[T, Abstraction[U, Abstraction[V, X]]], t: T, u: U, v: V
) -> R[X]:
    return FunctionThree.create(_, a)(t, u, v), a(t)(u)(v)


@register  # type: ignore
@rule
def zero_value(_: str, t: T) -> R[T]:
    return FunctionZero.create(_, t).value, t


@register  # type: ignore
@rule
def one_abstraction(fn: FunctionOne[T, U]) -> R[Abstraction[T, U]]:
    return fn.abstraction, lambda: Abstraction[T, U].from_fn(lambda t: fn(t))


@register  # type: ignore
@rule
def two_abstraction(fn: FunctionTwo[T, U, V]) -> R[Abstraction[T, Abstraction[U, V]]]:
    return (
        fn.abstraction,
        lambda: Abstraction[T, Abstraction[U, V]].from_fn(
            lambda t: Abstraction[U, V].from_fn(lambda u: fn(t, u))
        ),
    )


@register  # type: ignore
@rule
def three_abstraction(
    fn: FunctionThree[T, U, V, X]
) -> R[Abstraction[T, Abstraction[U, Abstraction[V, X]]]]:
    return (
        fn.abstraction,
        lambda: Abstraction[T, Abstraction[U, Abstraction[V, X]]].from_fn(
            lambda t: Abstraction[U, Abstraction[V, X]].from_fn(
                lambda u: Abstraction[V, X].from_fn(lambda v: fn(t, u, v))
            )
        ),
    )


@register  # type: ignore
@rule
def zero_name(name: str, t: T):
    return FunctionZero.create(name, t).name, name


@register  # type: ignore
@rule
def one_name(_: str, abst: Abstraction[T, U]):
    return FunctionOne.create(_, abst).name, _


@register  # type: ignore
@rule
def two_name(_: str, abst: Abstraction[T, Abstraction[U, V]]):
    return FunctionTwo.create(_, abst).name, _


@register  # type: ignore
@rule
def three_name(_: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]):
    return FunctionThree.create(_, abst).name, _


@register_pre  # type: ignore
@rule
def one_unfix(name: str, abst: Abstraction[T, U]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionOne[T, U]) -> FunctionOne[T, U]:
            return FunctionOne.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionOne.create(name, abst).unfix, result


@register_pre  # type: ignore
@rule
def two_unfix(name: str, abst: Abstraction[T, Abstraction[U, V]]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionTwo[T, U, V]) -> FunctionTwo[T, U, V]:
            return FunctionTwo.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionTwo.create(name, abst).unfix, result


@register_pre  # type: ignore
@rule
def three_unfix(name: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionThree[T, U, V, X]) -> FunctionThree[T, U, V, X]:
            return FunctionThree.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionThree.create(name, abst).unfix, result

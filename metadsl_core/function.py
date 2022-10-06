"""
This module is built on top of the abstraction

It adds the ability to have multiple arities and names attached to functions.

Because MyPy doesn't support multiple arity generics, we need a seperate class for each arity of
function.
"""
from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .conversion import *
from .maybe import *
from .strategies import *

__all__ = ["FunctionZero", "FunctionOne", "FunctionTwo", "FunctionThree"]


T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


class FunctionZero(Expression, typing.Generic[T], wrap_methods=True):
    """
    Function with zero args.
    """

    @classmethod
    def from_fn(cls, fn: typing.Callable[[], T]) -> FunctionZero[T]:
        return cls.create(fn.__name__, fn())

    def __call__(self) -> T:
        ...

    @classmethod
    def create(cls, name: str, val: T) -> FunctionZero[T]:
        ...

    @property  # type: ignore
    def value(self) -> T:
        ...

    @property
    def name(self) -> str:
        ...


class FunctionOne(Expression, typing.Generic[T, U], wrap_methods=True):
    """
    Function with one arg.
    """

    @classmethod
    def from_fn(
        cls, fn: typing.Callable[[T], U], name=Maybe[str].nothing()
    ) -> FunctionOne[T, U]:
        return cls.create(name.default(fn.__name__), Abstraction.from_fn(fn))

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

    def __call__(self, arg: T) -> U:
        ...

    @classmethod
    def create(cls, name: str, val: Abstraction[T, U]) -> FunctionOne[T, U]:
        ...

    @property
    def abstraction(self) -> Abstraction[T, U]:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def unfix(self) -> Abstraction[FunctionOne[T, U], FunctionOne[T, U]]:
        ...


class FunctionTwo(Expression, typing.Generic[T, U, V], wrap_methods=True):
    """
    Function with two args.
    """

    @classmethod
    def from_fn(cls, fn: typing.Callable[[T, U], V]) -> FunctionTwo[T, U, V]:
        def inner(arg1: T) -> Abstraction[U, V]:
            def inner(arg2: U) -> V:
                return fn(arg1, arg2)

            return Abstraction.from_fn(inner)

        return cls.create(fn.__name__, Abstraction.from_fn(inner))

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

    def __call__(self, arg1: T, arg2: U) -> V:
        ...

    @classmethod
    def create(
        cls, name: str, val: Abstraction[T, Abstraction[U, V]]
    ) -> FunctionTwo[T, U, V]:
        ...

    @property
    def abstraction(self) -> Abstraction[T, Abstraction[U, V]]:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def unfix(self) -> Abstraction[FunctionTwo[T, U, V], FunctionTwo[T, U, V]]:
        ...


class FunctionThree(Expression, typing.Generic[T, U, V, X], wrap_methods=True):
    """
    Function with three args.
    """

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

    def __call__(self, arg1: T, arg2: U, arg3: V) -> X:
        ...

    @classmethod
    def create(
        cls, name: str, val: Abstraction[T, Abstraction[U, Abstraction[V, X]]]
    ) -> FunctionThree[T, U, V, X]:
        ...

    @property
    def abstraction(self) -> Abstraction[T, Abstraction[U, Abstraction[V, X]]]:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def unfix(
        self,
    ) -> Abstraction[FunctionThree[T, U, V, X], FunctionThree[T, U, V, X]]:
        ...


register.pre(default_rule(FunctionZero[T].from_fn))
register.pre(default_rule(FunctionOne[T, U].from_fn))
register.pre(default_rule(FunctionTwo[T, U, V].from_fn))
register.pre(default_rule(FunctionThree[T, U, V, X].from_fn))


register.pre(default_rule(FunctionOne[T, U].from_fn_recursive))
register.pre(default_rule(FunctionTwo[T, U, V].from_fn_recursive))
register.pre(default_rule(FunctionThree[T, U, V, X].from_fn_recursive))


@register_ds  # type: ignore
@rule
def zero_call(_: str, v: T) -> R[T]:
    return FunctionZero.create(_, v)(), v


@register_ds  # type: ignore
@rule
def one_call(_: str, a: Abstraction[T, U], t: T) -> R[U]:
    return FunctionOne.create(_, a)(t), a(t)


@register_ds  # type: ignore
@rule
def two_call(_: str, a: Abstraction[T, Abstraction[U, V]], t: T, u: U) -> R[V]:
    return FunctionTwo.create(_, a)(t, u), a(t)(u)


@register_ds  # type: ignore
@rule
def three_call(
    _: str, a: Abstraction[T, Abstraction[U, Abstraction[V, X]]], t: T, u: U, v: V
) -> R[X]:
    return FunctionThree.create(_, a)(t, u, v), a(t)(u)(v)


@register_core  # type: ignore
@rule
def zero_value(_: str, t: T) -> R[T]:
    return FunctionZero.create(_, t).value, t


@register_core  # type: ignore
@rule
def one_abstraction(fn: FunctionOne[T, U]) -> R[Abstraction[T, U]]:
    return fn.abstraction, lambda: Abstraction[T, U].from_fn(lambda t: fn(t))


@register_core  # type: ignore
@rule
def two_abstraction(fn: FunctionTwo[T, U, V]) -> R[Abstraction[T, Abstraction[U, V]]]:
    return (
        fn.abstraction,
        lambda: Abstraction[T, Abstraction[U, V]].from_fn(
            lambda t: Abstraction[U, V].from_fn(lambda u: fn(t, u))
        ),
    )


@register_core  # type: ignore
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


@register_core  # type: ignore
@rule
def zero_name(name: str, t: T):
    return FunctionZero.create(name, t).name, name


@register_core  # type: ignore
@rule
def one_name(_: str, abst: Abstraction[T, U]):
    return FunctionOne.create(_, abst).name, _


@register_core  # type: ignore
@rule
def two_name(_: str, abst: Abstraction[T, Abstraction[U, V]]):
    return FunctionTwo.create(_, abst).name, _


@register_core  # type: ignore
@rule
def three_name(_: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]):
    return FunctionThree.create(_, abst).name, _


@register.pre  # type: ignore
@rule
def one_unfix(name: str, abst: Abstraction[T, U]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionOne[T, U]) -> FunctionOne[T, U]:
            return FunctionOne.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionOne.create(name, abst).unfix, result


@register.pre  # type: ignore
@rule
def two_unfix(name: str, abst: Abstraction[T, Abstraction[U, V]]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionTwo[T, U, V]) -> FunctionTwo[T, U, V]:
            return FunctionTwo.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionTwo.create(name, abst).unfix, result


@register.pre  # type: ignore
@rule
def three_unfix(name: str, abst: Abstraction[T, Abstraction[U, Abstraction[V, X]]]):
    def result():
        @Abstraction.from_fn
        def inner(fn: FunctionThree[T, U, V, X]) -> FunctionThree[T, U, V, X]:
            return FunctionThree.create(name, abst.unfix(fn.abstraction))

        return inner

    return FunctionThree.create(name, abst).unfix, result


@register_convert
@rule
def function_zero_convert(
    name: str,
    callable_zero: typing.Callable[[], T],
    value: T,
    # callable_one: typing.Callable[[T], U],
    # abs_one: Abstraction[T, U],
) -> R[Maybe[FunctionZero[Maybe[U]]]]:
    # From callable -> function
    yield (
        Converter[FunctionZero[Maybe[U]]].convert(callable_zero),
        lambda: Converter[FunctionZero[Maybe[U]]].convert(
            FunctionZero.from_fn(callable_zero)
        ),
    )
    # from function -> value
    yield (
        Converter[FunctionZero[Maybe[U]]].convert(FunctionZero.create(name, value)),
        Maybe.just(FunctionZero.create(name, Converter[U].convert(value))),
    )


@register_convert
@rule
def function_one_convert(
    name: str, callable_one: typing.Callable[[T], U], abs_one: Abstraction[T, U],
) -> R[Maybe[FunctionOne[V, Maybe[X]]]]:
    yield (
        Converter[FunctionOne[V, Maybe[X]]].convert(callable_one),
        lambda: Converter[FunctionOne[V, Maybe[X]]].convert(
            FunctionOne.from_fn(callable_one)
        ),
    )
    yield (
        Converter[FunctionOne[V, Maybe[X]]].convert(FunctionOne.create(name, abs_one)),
        lambda: Converter[Abstraction[V, Maybe[X]]]
        .convert(abs_one)
        .map(
            Abstraction[Abstraction[V, Maybe[X]], FunctionOne[V, Maybe[X]]].from_fn(
                lambda converted_abs: FunctionOne.create(name, converted_abs)
            )
        ),
    )


@register_convert
@rule
def convert_fn_to_abstraction(
    a: typing.Callable[[T], U]
) -> R[Maybe[Abstraction[V, Maybe[X]]]]:
    return (
        Converter[Abstraction[V, Maybe[X]]].convert(a),
        lambda: Converter[Abstraction[V, Maybe[X]]].convert(Abstraction.from_fn(a)),
    )

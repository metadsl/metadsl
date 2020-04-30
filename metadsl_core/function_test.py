from __future__ import annotations

import metadsl.typing_tools
import pytest
from metadsl import *

from metadsl_rewrite import *

from .abstraction import *
from .conversion import *
from .function import *
from .integer import *
from .maybe import *
from .strategies import *

one = Integer.from_int(1)
zero = Integer.from_int(0)


class TestFunction:
    def test_zero_abstraction(self):
        @FunctionZero.from_fn
        def fn() -> Integer:
            return one

        assert execute(fn()) == one

    def test_one_abstraction(self):
        @FunctionOne.from_fn
        def add_one(a: Integer) -> Integer:
            return a + one

        assert (
            metadsl.typing_tools.get_type(execute(add_one.abstraction))
            == Abstraction[Integer, Integer]
        )

        assert execute(add_one.abstraction(zero)) == one

    def test_one_recursive_call(self):
        @FunctionOne.from_fn_recursive
        def factorial(fact_fn: FunctionOne[Integer, Integer], n: Integer) -> Integer:
            return n.eq(zero).if_(one, n * fact_fn(n - one))

        assert execute(factorial(zero)) == one
        assert execute(factorial(one)) == one
        assert execute(factorial(Integer.from_int(3))) == Integer.from_int(6)

    def test_two_abstraction(self):
        @FunctionTwo.from_fn
        def add(a: Integer, b: Integer) -> Integer:
            return a + b

        assert (
            metadsl.typing_tools.get_type(execute(add.abstraction))
            == Abstraction[Integer, Abstraction[Integer, Integer]]
        )

        assert execute(add.abstraction(one)(zero)) == one

    def test_two_call(self):
        @FunctionTwo.from_fn
        def add(a: Integer, b: Integer) -> Integer:
            return a + b

        assert execute(
            add(Integer.from_int(1), Integer.from_int(2))
        ) == Integer.from_int(3)

    def test_three_recursive_call(self):
        @FunctionThree.from_fn_recursive
        def fib_more(
            fn: FunctionThree[Integer, Integer, Integer, Integer],
            n: Integer,
            a: Integer,
            b: Integer,
        ) -> Integer:
            pred_cont = n > one
            minus1 = n - one
            ab = a + b
            added = fn(minus1, b, ab)

            n_eq_1 = n.eq(one)
            return pred_cont.if_(added, n_eq_1.if_(b, a))

        @FunctionOne.from_fn
        def fib(n: Integer) -> Integer:
            return fib_more(n, zero, one)

        assert execute(fib(zero)) == zero
        assert execute(fib(one)) == one
        assert execute(fib(Integer.from_int(8))) == Integer.from_int(21)


class T(Expression):
    ...


class U(Expression):
    ...


class V(Expression):
    ...


class X(Expression):
    ...


@expression
def t_to_u(t: T) -> U:
    ...


@expression
def t() -> T:
    ...


@expression
def v() -> V:
    ...


@expression
def v_to_t(v: V) -> T:
    ...


@expression
def u_to_x(u: U) -> X:
    ...


@rule
def convert_t_to_u_just(t: T) -> R[Maybe[U]]:
    return Converter[U].convert(t), Maybe.just(t_to_u(t))


@rule
def convert_t_to_u_nothing(t: T) -> R[Maybe[U]]:
    return Converter[U].convert(t), Maybe[U].nothing()


def fn() -> T:
    return t()


def fn_one(t: T) -> U:
    return t_to_u(t)


@rule
def convert_v_to_t_just(v: V) -> R[Maybe[T]]:
    return Converter[T].convert(v), Maybe.just(v_to_t(v))


@rule
def convert_v_to_t_nothing(v: V) -> R[Maybe[T]]:
    return Converter[T].convert(v), Maybe[T].nothing()


@rule
def convert_u_to_x_just(u: U) -> R[Maybe[X]]:
    return Converter[X].convert(u), Maybe.just(u_to_x(u))


@rule
def convert_u_to_x_nothing(u: U) -> R[Maybe[X]]:
    return Converter[X].convert(u), Maybe[X].nothing()


class TestFunctionConversion:
    @pytest.mark.parametrize(
        "t_to_u_rule",
        [convert_t_to_u_just, convert_t_to_u_nothing],
        ids=["just", "nothing"],
    )
    @pytest.mark.parametrize(
        "input",
        [fn, FunctionZero[T].from_fn(fn)],
        ids=["python function", "FunctionZero"],
    )
    def test_zero(self, input, t_to_u_rule):
        result = Converter[FunctionZero[Maybe[U]]].convert(input)
        desired = Maybe.just(FunctionZero.create("fn", Converter[U].convert(t())))
        with register.tmp(t_to_u_rule):
            assert execute(result) == execute(desired)

    @pytest.mark.parametrize(
        "u_to_x_rule",
        [convert_v_to_t_just, convert_u_to_x_nothing],
        ids=["just", "nothing"],
    )
    @pytest.mark.parametrize(
        "v_to_t_rule",
        [convert_v_to_t_just, convert_v_to_t_nothing],
        ids=["just", "nothing"],
    )
    @pytest.mark.parametrize(
        "input",
        [fn_one, FunctionOne[T, U].from_fn(fn_one)],
        ids=["python function", "FunctionOne"],
    )
    def test_one(self, input, u_to_x_rule, v_to_t_rule):
        converted_fn = Converter[FunctionOne[V, Maybe[X]]].convert(input)
        result: Maybe[X] = converted_fn.flat_map(
            Abstraction[FunctionOne[V, Maybe[X]], Maybe[X]].from_fn(lambda fn: fn(v()))
        )

        desired: Maybe[X] = Converter[T].convert(v()).map(
            Abstraction[T, U].from_fn(fn_one)
        ).flat_map(Abstraction[U, Maybe[X]].from_fn(Converter[X].convert))

        with register.tmp(u_to_x_rule, v_to_t_rule):
            assert execute(result) == execute(desired)

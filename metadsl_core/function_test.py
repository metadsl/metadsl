from __future__ import annotations

from metadsl import *
import metadsl.typing_tools
from .function import *
from .integer import *
from .abstraction import *

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

from __future__ import annotations

from metadsl import *
import metadsl.typing_tools
from .function import *
from .integer import *
from .abstraction import *


class TestFunction:
    def test_one_recursive_call(self):

        one = Integer.from_int(1)
        zero = Integer.from_int(0)

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
            metadsl.typing_tools.get_type(execute(add.abstraction()))
            == Abstraction[Integer, Abstraction[Integer, Integer]]
        )

    def test_two_call(self):
        @FunctionTwo.from_fn
        def add(a: Integer, b: Integer) -> Integer:
            return a + b

        assert execute(
            add(Integer.from_int(1), Integer.from_int(2))
        ) == Integer.from_int(3)

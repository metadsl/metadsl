from __future__ import annotations

import typing

from metadsl import *
from .rules import *
from .abstraction import *
from .abstraction import Variable, from_fn_rule
from .integer import *


T = typing.TypeVar("T")


class I(Expression):
    @expression
    @classmethod
    def create(cls, i: int) -> I:
        ...

    @expression
    def inc(self) -> I:
        ...

    @expression
    def dec(self) -> I:
        ...


class TestAbstraction:
    def test_from_fn(self):
        a = execute(Abstraction[typing.Any, int].from_fn(lambda i: i), from_fn_rule)
        assert isinstance(a, Abstraction)
        assert a.function == Abstraction[typing.Any, int].create
        var, body = a.args
        assert (
            var.function == Abstraction[typing.Any, int].create_variable  # type: ignore
        )
        (var_,) = var.args  # type: ignore
        assert isinstance(var_, Variable)
        assert body == var

    def test_constant(self):
        assert execute(Abstraction[typing.Any, int].from_fn(lambda _: 10)("hi")) == 10

    def test_identity(self):
        assert execute(Abstraction[str, str].from_fn(lambda i: i)("hi")) == "hi"

    def test_compose(self):
        assert execute(
            (Abstraction.from_fn(I.inc) + Abstraction.from_fn(I.dec))(I.create(10))
        ) == I.inc(I.dec(I.create(10)))

    def test_fix(self):
        one = Integer.from_int(1)
        zero = Integer.from_int(0)

        @Abstraction.fix
        @Abstraction.from_fn
        def factorial(
            fact_fn: Abstraction[Integer, Integer]
        ) -> Abstraction[Integer, Integer]:
            @Abstraction.from_fn
            def inner(n: Integer) -> Integer:
                return n.eq(zero).if_(one, n * fact_fn(n - one))

            return inner

        assert execute(factorial(zero)) == one
        assert execute(factorial(one)) == one
        assert execute(factorial(Integer.from_int(2))) == Integer.from_int(2)
        assert execute(factorial(Integer.from_int(3))) == Integer.from_int(6)

    def test_unfix_fixed(self):
        one = Integer.from_int(1)
        zero = Integer.from_int(0)

        @Abstraction.fix
        @Abstraction.unfix
        @Abstraction.fix
        @Abstraction.from_fn
        def factorial(
            fact_fn: Abstraction[Integer, Integer]
        ) -> Abstraction[Integer, Integer]:
            @Abstraction.from_fn
            def inner(n: Integer) -> Integer:
                return n.eq(zero).if_(one, n * fact_fn(n - one))

            return inner

        assert execute(factorial(zero)) == one
        assert execute(factorial(one)) == one

    def test_unfix_not_fixed(self):
        two = Integer.from_int(2)
        one = Integer.from_int(1)
        zero = Integer.from_int(0)

        @Abstraction.from_fn
        def add_one(i: Integer) -> Integer:
            return i + one

        @Abstraction.from_fn
        def add_two(i: Integer) -> Integer:
            return i + one + one

        assert execute(Abstraction.unfix(add_one)(add_one)(zero)) == one
        assert execute(Abstraction.unfix(add_two)(add_one)(zero)) == two

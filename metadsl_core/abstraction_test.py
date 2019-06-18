import typing

from metadsl import default_rule
from .rules import *
from .abstraction import *
from .abstraction import Variable


class TestAbstraction:
    def test_from_fn(self):
        a = default_rule(Abstraction.from_fn)(
            Abstraction[typing.Any, int].from_fn(lambda i: i)
        )
        assert isinstance(a, Abstraction)
        assert a.function == Abstraction.create.__exposed__  # type: ignore
        var, body = a.args
        assert var.function == Abstraction.create_variable.__exposed__  # type: ignore
        var_, = var.args  # type: ignore
        assert isinstance(var_, Variable)
        assert body == var

    def test_constant(self):
        assert rules(Abstraction[typing.Any, int].from_fn(lambda _: 10)("hi")) == 10

import typing

from metadsl import default_rule, execute_rule
from .rules import *
from .abstraction import *
from .abstraction import Variable, from_fn_rule


T = typing.TypeVar("T")


class TestAbstraction:
    def test_from_fn(self):
        a = execute_rule(
            from_fn_rule, Abstraction[typing.Any, int].from_fn(lambda i: i)
        )
        assert isinstance(a, Abstraction)
        assert a.function == Abstraction[typing.Any, int].create
        var, body = a.args
        assert (
            var.function == Abstraction[typing.Any, int].create_variable  # type: ignore
        )
        var_, = var.args  # type: ignore
        assert isinstance(var_, Variable)
        assert body == var

    def test_constant(self):
        assert (
            execute_rule(
                core_rules, Abstraction[typing.Any, int].from_fn(lambda _: 10)("hi")
            )
            == 10
        )

    def test_identity(self):
        assert (
            execute_rule(core_rules, Abstraction[T, T].from_fn(lambda i: i)("hi"))
            == "hi"
        )

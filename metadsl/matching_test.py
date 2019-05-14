from __future__ import annotations
import typing
from .matching import *
from .typing_tools import *
from .expressions import *


class _SomeExpression(Expression):
    pass


class TestWildcard:
    def test_create_literal(self):
        w = create_wildcard(E[int])  # type: ignore
        assert get_type(w) == LiteralExpression[int]
        assert isinstance(extract_wildcard(w), Wildcard)

    def test_create_expression(self):
        w = create_wildcard(_SomeExpression)
        assert get_type(w) == _SomeExpression
        assert isinstance(extract_wildcard(w), Wildcard)


class _Number(Expression):
    @expression
    def __add__(self, other: _Number) -> _Number:
        ...


@expression
def _from_int(i: E[int]) -> _Number:
    ...


@rule
def _add_rule(a: E[int], b: E[int]) -> typing.Tuple[_Number, typing.Optional[_Number]]:
    return (
        _from_int(a) + _from_int(b),
        _from_int(a + b) if isinstance(a, int) and isinstance(b, int) else None,
    )


class TestRule:
    def test_add(self):
        expr = _from_int(1) + _from_int(2)
        assert _add_rule(expr) == _from_int(3)


@expression
def _from_str(s: E[str]) -> _Number:
    ...


@rule
def _add_zero_rule(a: _Number) -> typing.Tuple[_Number, _Number]:
    return a + _from_int(0), a


class TestPureRule:
    def test_add_zero(self):
        s = _from_str("str")
        expr = s + _from_int(0)
        assert _add_zero_rule(expr) == s

from __future__ import annotations
import typing
from .matching import *
from .typing_tools import *
from .expressions import *


class _SomeExpression(Expression):
    pass


class TestWildcard:
    def test_create_literal(self):
        w = create_wildcard(int)  # type: ignore
        assert get_type(w) == PlaceholderExpression[int]

    def test_create_expression(self):
        w = create_wildcard(_SomeExpression)
        assert get_type(w) == _SomeExpression


class _Number(Expression):
    @expression
    def __add__(self, other: _Number) -> _Number:
        ...


@expression
def _from_int(i: int) -> _Number:
    ...


@rule
def _add_rule(a: int, b: int) -> R[_Number]:
    return (_from_int(a) + _from_int(b), lambda: _from_int(a + b))


T = typing.TypeVar("T")


class _List(Expression, typing.Generic[T]):
    @expression
    def __add__(self, other: _List[T]) -> _List[T]:
        ...


@expression
def _list(item_type: typing.Type[T], *items: T) -> _List[T]:
    ...


class TestRule:
    def test_add(self):
        expr = _from_int(1) + _from_int(2)
        assert _add_rule(expr) == _from_int(3)

    def test_type_args(self):
        @rule
        def _concat_lists(tp: typing.Type[T], l: T, r: T) -> R[_List[T]]:
            return _list(tp, l) + _list(tp, r), lambda: _list(tp, l, r)

        assert _concat_lists(_list(int, 1) + _list(int, 2)) == _list(int, 1, 2)

    def test_variable_args(self):
        @rule
        def _concat_lists(
            tp: typing.Type[T], ls: typing.Iterable[T], rs: typing.Iterable[T]
        ) -> R[_List[T]]:
            return _list(tp, *ls) + _list(tp, *rs), lambda: _list(tp, *ls, *rs)

        assert _concat_lists(_list(int, 1, 2) + _list(int, 3, 4)) == _list(
            int, 1, 2, 3, 4
        )

    def test_variable_args_right_side(self):
        @rule
        def _concat_lists_minus_end(
            tp: typing.Type[T],
            ls: typing.Iterable[T],
            rs: typing.Iterable[T],
            l: T,
            r: T,
        ) -> R[_List[T]]:
            return _list(tp, *ls, l) + _list(tp, *rs, r), lambda: _list(tp, *ls, *rs)

        assert _concat_lists_minus_end(_list(int, 1, 2) + _list(int, 3, 4)) == _list(
            int, 1, 3
        )


@expression
def _from_str(s: str) -> _Number:
    ...


@rule
def _add_zero_rule(a: _Number) -> R[_Number]:
    return a + _from_int(0), lambda: a


class TestPureRule:
    def test_add_zero(self):
        s = _from_str("str")
        expr = s + _from_int(0)
        assert _add_zero_rule(expr) == s


# TODO:
# Update python and numpy examples
# Update notebooks


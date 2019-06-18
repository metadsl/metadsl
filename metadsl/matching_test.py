from __future__ import annotations
import typing
from .matching import *
from .rules import execute_rule
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
    @classmethod
    def create(cls, *items: T) -> _List[T]:
        ...


class TestRule:
    def test_add(self):
        expr = _from_int(1) + _from_int(2)
        assert execute_rule(_add_rule, expr) == _from_int(3)

    def test_type_args(self):
        @rule
        def _concat_lists(l: T, r: T) -> R[_List[T]]:
            return _List.create(l) + _List.create(r), lambda: _List.create(l, r)

        assert execute_rule(
            _concat_lists, _List.create(1) + _List.create(2)
        ) == _List.create(1, 2)

    def test_variable_args(self):
        @rule
        def _concat_lists(
            ls: typing.Iterable[T], rs: typing.Iterable[T]
        ) -> R[_List[T]]:
            return (
                _List[T].create(*ls) + _List[T].create(*rs),
                lambda: _List[T].create(*ls, *rs),
            )

        assert execute_rule(
            _concat_lists, _List.create(1, 2) + _List.create(3, 4)
        ) == _List.create(1, 2, 3, 4)

    def test_variable_args_empty(self):
        @rule
        def _concat_lists(
            ls: typing.Iterable[T], rs: typing.Iterable[T]
        ) -> R[_List[T]]:
            return (
                _List[T].create(*ls) + _List[T].create(*rs),
                lambda: _List[T].create(*ls, *rs),
            )

        assert (
            execute_rule(_concat_lists, _List[int].create() + _List[int].create())
            == _List[int].create()
        )

    def test_variable_args_right_side(self):
        @rule
        def _concat_lists_minus_end(
            ls: typing.Iterable[T], rs: typing.Iterable[T], l: T, r: T
        ) -> R[_List[T]]:
            return (
                _List[T].create(*ls, l) + _List[T].create(*rs, r),
                lambda: _List[T].create(*ls, *rs),
            )

        assert execute_rule(
            _concat_lists_minus_end, _List.create(1, 2) + _List.create(3, 4)
        ) == _List.create(1, 3)

        assert (
            execute_rule(_concat_lists_minus_end, _List.create(1) + _List.create(3))
            == _List[int].create()
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
        assert execute_rule(_add_zero_rule, expr) == s


class TestDefaultRule:
    def test_fn(self):
        @expression
        def inner_fn(a: int) -> Expression:
            ...

        @expression
        def fn(a: int) -> Expression:
            return inner_fn(a)

        assert fn(10) != inner_fn(10)
        assert execute_rule(default_rule(fn), fn(10)) == inner_fn(10)

    def test_method(self):
        class C(Expression):
            @expression
            def __add__(self, other: C) -> C:
                ...

            @expression
            def double(self) -> C:
                return self + self

        globals()["C"] = C

        @expression
        def create() -> C:
            ...

        rule = default_rule(C.double)
        assert create().double() != create() + create()
        assert execute_rule(rule, create().double()) == create() + create()

    def test_method_generic(self):
        class C(Expression, typing.Generic[T]):
            @expression
            def __add__(self, other: C[T]) -> C[T]:
                ...

            @expression
            def double(self) -> C[T]:
                return self + self

            @expression
            @classmethod
            def create(cls) -> C[T]:
                ...

        globals()["C"] = C

        expr = C[int].create().double()

        rule = default_rule(C.double)
        assert execute_rule(rule, expr) == C[int].create() + C[int].create()

        assert execute_rule(rule, expr) != C[str].create() + C[str].create()
        assert expr != C[int].create() + C[int].create()

    def test_classmethod_generic(self):
        class C(Expression, typing.Generic[T]):
            @expression
            @classmethod
            def create(cls) -> C[T]:
                ...

            @expression
            @classmethod
            def create_wrapper(cls) -> C[T]:
                return cls.create()

        globals()["C"] = C

        expr = C[int].create_wrapper()
        rule = default_rule(C.create_wrapper)

        assert execute_rule(rule, expr) == C[int].create()

        assert execute_rule(rule, expr) != C[str].create()
        assert expr != C[int].create()

    def test_classmethod_generic_arg(self):
        class C(Expression, typing.Generic[T]):
            @expression
            @classmethod
            def create(cls, v: T) -> C[T]:
                ...

            @expression
            @classmethod
            def create_wrapper(cls, v: T) -> C[T]:
                return cls.create(v)

        globals()["C"] = C

        expr = C.create_wrapper(123)
        rule = default_rule(C.create_wrapper)
        assert execute_rule(rule, expr) == C.create(123)

        assert expr != C.create(123)

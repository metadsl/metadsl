from __future__ import annotations

import typing

from .wraps import *
from .expressions import *


class SomeExpr(Expression):
    pass


@expression
def create() -> SomeExpr:
    ...


@expression
def create_expr() -> Expression:
    ...


@expression
def fn(a: SomeExpr, b: Expression) -> SomeExpr:
    ...


class SomeWrap(Wrap[SomeExpr]):
    pass


@wrap(fn)
def fn_wrapped(a: object, b: object) -> SomeWrap:
    ...


def test_wrap_function():
    result = fn_wrapped(SomeWrap(create()), create_expr())
    assert result == SomeWrap(SomeExpr(fn, (create(), create_expr())))


T = typing.TypeVar("T")


class Expr(Expression, typing.Generic[T]):
    pass


class WrapExpr(Wrap[Expr[T]]):
    ...


@expression
def create_int() -> Expr[int]:
    ...


@wrap(create_int)
def wrapped_create_int() -> WrapExpr[int]:
    ...


def test_wrap_returns_generic():
    assert wrapped_create_int() == WrapExpr[int](Expr[int](create_int, tuple()))


class Number(Expression):
    @expression
    def __add__(self, other: Number) -> Number:
        ...


@expression
def create_number() -> Number:
    ...


class WrapNumber(Wrap[Number]):
    @wrap(Number.__add__)
    def __add__(self, other: object) -> WrapNumber:
        ...


def test_wrap_method():
    n = create_number()
    k = create_number()
    assert WrapNumber(n) + k == WrapNumber(n + k)


class List(Expression, typing.Generic[T]):
    @expression
    def __getitem__(self, idx: Number) -> T:
        ...


@expression
def create_list_number() -> List[Number]:
    ...


class WrapListInt(Wrap[List[Number]]):
    @wrap(List.__getitem__)
    def __getitem__(self, idx: object) -> WrapNumber:
        ...


def test_wrap_method_generic():
    l = create_list_number()
    i = create_number()
    assert WrapListInt(l)[i] == WrapNumber(l[i])

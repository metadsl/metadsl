from __future__ import annotations

import typing

import pytest

from .expressions import *
from .expressions_test import TEST_EXPRESSIONS
from .normalized import *
from .normalized import Graph, graph_str


@pytest.mark.parametrize("expr", TEST_EXPRESSIONS)
def test_expression_reference_identity(expr):
    ref = ExpressionReference.from_expression(expr)
    assert ref.expression == expr


@expression
def a(e: typing.Any) -> typing.Any:
    ...


@expression
def b(e: typing.Any) -> typing.Any:
    ...


@expression
def c() -> typing.Any:
    ...


@expression
def d() -> typing.Any:
    ...


def test_replace():
    ref = ExpressionReference.from_expression(a(b(c())))

    assert tuple(child.expression for child in ref.descendents) == (
        c(),
        b(c()),
        a(b(c())),
    )

    ref.replace(a(b(d())))

    assert ref.expression == a(b(d()))

    assert tuple(child.expression for child in ref.descendents) == (
        d(),
        b(d()),
        a(b(d())),
    )


def test_replace_child():
    ref = ExpressionReference.from_expression(a(b(c())))

    assert tuple(child.expression for child in ref.descendents) == (
        c(),
        b(c()),
        a(b(c())),
    )

    child_ref = list(ref.descendents)[0]
    child_ref.replace(d())

    assert ref.expression == a(b(d()))

    assert tuple(child.expression for child in ref.descendents) == (
        d(),
        b(d()),
        a(b(d())),
    )


@expression
def e(a: typing.Any, b: typing.Any) -> typing.Any:
    ...


@expression
def f(e: typing.Any) -> typing.Any:
    ...


@expression
def g(e: typing.Any) -> typing.Any:
    ...


def test_graph_subtree():
    """
    Verify processed in correct order
    """
    orig = e(f(g(d())), d())
    ref = ExpressionReference.from_expression(orig)
    assert ref.expression == orig


def test_doesnt_remember_replacements():
    ref = ExpressionReference.from_expression(a(b(c())))
    ref.replace(a(b(d())))
    ref.replace(a(b(c())))

    assert ref.expression == a(b(c()))


class E(Expression):
    @expression
    @classmethod
    def create(cls) -> E:
        ...
    
    @expression
    def method(self, other: typing.Any) -> typing.Any:
        ... 

    @expression
    def __getitem__(self, key: typing.Any) -> typing.Any:
        ...

@pytest.mark.parametrize(
    "expr,s",
    [
        pytest.param(1, "1", id="primitive top level"),
        pytest.param(c(), "c()", id="single"),
        pytest.param(b(c()), "b(c())", id="nested"),
        pytest.param(e(c(), c()), "any_0 = c()\ne(any_0, any_0)", id="temp"),
        pytest.param(e(E.create(), E.create()), "e_0 = E.create()\ne(e_0, e_0)", id="temp_with_tp"),
        pytest.param(E.create(), "E.create()", id="class method"),
        pytest.param(E.create().method(c()), "E.create().method(c())", id="instance method"),
        pytest.param(E.create()[c()], "E.create()[c()]", id="getitem method"),
    ],
)
def test_graph_str(expr, s):
    assert graph_str(Graph(expr)) == s

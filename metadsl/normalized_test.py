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


@pytest.mark.parametrize(
    "expr,s",
    [
        pytest.param(1, "1", id="primitive top level"),
        pytest.param(c(), "c()", id="single"),
        pytest.param(b(c()), "b(c())", id="nested"),
        pytest.param(e(c(), c()), "_0 = c()\ne(_0, _0)", id="temp"),
    ],
)
def test_graph_str(expr, s):
    assert graph_str(Graph(expr)) == s

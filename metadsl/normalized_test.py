from __future__ import annotations

import pytest
import typing

from .expressions import *
from .normalized import *
from .expressions_test import TEST_EXPRESSIONS


@pytest.mark.parametrize("expr", TEST_EXPRESSIONS)
def test_expression_reference_identity(expr):
    ref = ExpressionReference.from_expression(expr)
    ref.verify_integrity()
    assert ref.normalized_expression.value == expr


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
    ref.verify_integrity()
    original_hashes, original_expr = zip(
        *((child.hash, child.normalized_expression.value,) for child in ref.children)
    )

    assert original_expr == (a(b(c())), b(c()), c())

    ref.replace(a(b(d())))
    ref.verify_integrity()

    new_hashes, new_expr = zip(
        *((child.hash, child.normalized_expression.value,) for child in ref.children)
    )

    assert new_expr == (a(b(d())), b(d()), d())

    # None of the hashes should be the same
    for i in (0, 1, 2):
        assert original_hashes[i] != new_hashes[i]


def test_replace_child():
    ref = ExpressionReference.from_expression(a(b(c())))

    ref.verify_integrity()

    original_hashes, original_expr = zip(
        *((child.hash, child.normalized_expression.value,) for child in ref.children)
    )

    assert original_expr == (a(b(c())), b(c()), c())
    child_ref = list(ref.children)[-1]
    child_ref.replace(d())
    child_ref.verify_integrity()

    ref.verify_integrity()

    new_hashes, new_expr = zip(
        *((child.hash, child.normalized_expression.value,) for child in ref.children)
    )

    assert new_expr == (a(b(d())), b(d()), d())

    # None of the hashes should be the same
    for i in (0, 1, 2):
        assert original_hashes[i] != new_hashes[i]


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
    ref.verify_integrity()
    assert ref.normalized_expression.value == orig


def test_doesnt_remember_replacements():
    ref = ExpressionReference.from_expression(a(b(c())))
    ref.verify_integrity()
    ref.replace(a(b(d())))
    ref.verify_integrity()
    ref.replace(a(b(c())))
    ref.verify_integrity()

    assert ref.normalized_expression.value == a(b(c()))

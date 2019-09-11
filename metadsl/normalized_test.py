from __future__ import annotations

import pytest
import typing

from .expressions import *
from .normalized import *
from .expressions_test import TEST_EXPRESSIONS


@pytest.mark.parametrize("expr", TEST_EXPRESSIONS)
def test_expression_reference_identity(expr):
    assert ExpressionReference.from_expression(expr).to_expression() == expr


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
    original_hash = ref.hash
    original_hashes = list(ref.expressions.bfs(ref.hash))
    ref.replace(a(b(d())))
    final_hashes = list(ref.expressions.bfs(ref.hash))

    assert original_hash != ref.hash
    # None of the hashes should be the same
    for i in (0, 1, 2):
        assert original_hashes[i] != final_hashes[i]

    # the ids should be the  same
    for i in (0, 1, 2):
        assert (
            ref.expressions.hashes[original_hashes[i]]
            == ref.expressions.hashes[final_hashes[i]]
        )


def test_subtree():
    ref = ExpressionReference.from_expression(a(b(c())))
    original_hashes = list(ref.expressions.bfs(ref.hash))

    last_ref = list(ref.child_references())[-1]
    last_ref.replace(d())

    ref.replace(ref.to_expression())
    final_hashes = list(ref.expressions.bfs(ref.hash))

    # None of the hashes should be the same
    for i in (0, 1, 2):
        assert original_hashes[i] != final_hashes[i]

    # the ids should be the  same
    for i in (0, 1, 2):
        assert (
            ref.expressions.hashes[original_hashes[i]]
            == ref.expressions.hashes[final_hashes[i]]
        )


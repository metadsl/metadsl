from __future__ import annotations


import pytest


from .normalized import *
from .expressions_test import TEST_EXPRESSIONS


@pytest.mark.parametrize("expr", TEST_EXPRESSIONS)
def test_expression_reference_identity(expr):
    assert ExpressionReference.from_expression(expr).to_expression() == expr

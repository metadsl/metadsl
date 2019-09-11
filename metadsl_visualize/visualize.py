import IPython.core.display
import IPython
import typing

import typez
from metadsl import *
from .typez import *

__all__ = ["execute_and_visualize"]


T = typing.TypeVar("T")


def execute_and_visualize(ref: ExpressionReference, rule: Rule) -> object:
    """
    Returns the replaced version of this expression and also displays the execution trace.
    """

    typez_display = typez.TypezDisplay(typez.Typez())
    IPython.core.display.display(typez_display)
    # Update the typez display as we execute the rules
    for typez_ in convert_rule(rule)(ref):
        typez_display.typez = typez_
    return ref.to_expression()


def monkeypatch():
    """
    Monkeypatches Expression should it displays the result as well as each intermediate step.
    """
    Expression._ipython_display_ = _expression_ipython_display  # type: ignore
    # only change if we are in a kernel
    if IPython.get_ipython():
        execute.execute = execute_and_visualize  # type: ignore


def _expression_ipython_display(self):
    res = execute(self)
    # Only display result if we get back a non expression object
    if not isinstance(res, Expression):
        IPython.core.display.display(res)


monkeypatch()

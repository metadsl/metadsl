import typing
import IPython.core.display


import typez
from metadsl import *
from .typez import *

__all__ = ["set_rule", "execute_and_visualize"]


DEFAULT_RULE = None


def set_rule(rule: Rule):
    """
    Set's the global default rule to use for visualization.
    """
    global DEFAULT_RULE
    DEFAULT_RULE = rule


def execute_and_visualize(expr: object, rule=None):
    """
    Returns the replaced version of this expression and also displays the execution trace.
    """
    if not rule:
        rule = DEFAULT_RULE
    typez_display = typez.TypezDisplay(typez.Typez())
    IPython.core.display.display(typez_display)
    # Update the typez display as we execute the rules
    for expr, typez_ in convert_rule(rule)(expr):
        typez_display.typez = typez_
    return expr


def monkeypatch():
    """
    Monkeypatches Expression should it displays the result as well as each intermediate step.
    """
    Expression._ipython_display_ = _expression_ipython_display  # type: ignore


def _expression_ipython_display(self):
    assert DEFAULT_RULE
    IPython.core.display.display(execute_and_visualize(self))


monkeypatch()

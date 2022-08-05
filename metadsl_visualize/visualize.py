import typing

import IPython
import IPython.core.display
from metadsl import *
from metadsl_rewrite import *

from .typez import *

__all__ = ["execute_and_visualize"]


T = typing.TypeVar("T")


def execute_and_visualize(ref: ExpressionReference, strategy: Strategy) -> object:
    """
    Returns the replaced version of this expression and also displays the execution trace.
    """
    expression_display = ExpressionDisplay(ref)

    # Only display expressions if in notebook, not in shell
    if (
        IPython.get_ipython()
        and IPython.get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    ):
        IPython.core.display.display(expression_display)

    # Update the typez display as we execute the strategys
    for result in strategy(ref):
        expression_display.update(result)
    return ref.expression


def monkeypatch():
    """
    Monkeypatches execute so that it also displays each step
    """
    # only change if we are in a kernel
    if IPython.get_ipython():
        execute.execute = execute_and_visualize  # type: ignore


monkeypatch()

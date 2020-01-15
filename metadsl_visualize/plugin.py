# import typing

# Import visualize so uses custom execution if in ipython
from . import visualize


def pytest_assertrepr_compare(op, left, right):
    pass
    # import graphviz
    # from .visualize import visualize
    # from metadsl import Expression

    # if op == "==" and (isinstance(left, Expression) or isinstance(right, Expression)):
    #     d = graphviz.Digraph()
    #     seen: typing.Set[int] = set()
    #     visualize(left, d, seen)
    #     visualize(right, d, seen)
    #     d.render(cleanup=True, view=True)

    #     return [f"{left!r} != {right!r}"]

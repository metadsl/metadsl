from __future__ import annotations

import dataclasses
import typing

from metadsl import *

from .strategies import *

__all__ = [
    "StrategyFold",
    "StrategySequence",
    "StrategyLabel",
    "StrategyRepeat",
    "StrategyInOrder",
]


@dataclasses.dataclass
class StrategyLabel(Strategy):
    """
    Takes in an existing strategy and makes the final state have a label.
    """

    label: str
    strategy: Strategy

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        replaced = False
        for result in self.strategy(expr):
            replaced = True
            yield result
        if replaced:
            yield Result(name=self.label, label=self.label)

    def optimize(self, executor, strategy):
        self.strategy.optimize(executor, strategy)


@dataclasses.dataclass(init=False)
class StrategyInOrder(Strategy):
    """
    Returns a new replacement strategy that executes each of the strategies in order,
    returning a new expression if any of them replaced.
    """

    strategies: typing.Tuple[Strategy, ...]

    def __init__(self, *strategies: Strategy):
        self.strategies = strategies

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        for strategy in self.strategies:
            for replacement in strategy(expr):
                yield replacement

    def optimize(self, executor, strategy):
        for strategy_ in self.strategies:
            strategy_.optimize(executor, strategy)


@dataclasses.dataclass(init=False)
class StrategySequence(Strategy):
    """
    Returns a new replacement strategy that tries each of the replacement strategies in sequence, returning the result of the first that matches.
    """

    strategies: typing.Tuple[Strategy, ...]

    def __init__(self, *strategies: Strategy):
        self.strategies = strategies

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        for strategy in self.strategies:
            for replacement in strategy(expr):
                yield replacement
                return

    def optimize(self, executor, strategy):
        for strategy_ in self.strategies:
            strategy_.optimize(executor, strategy)


@dataclasses.dataclass
class StrategyFold(Strategy):
    """
    Returns the first replacement found by starting at the top of the expression tree
    and then recursing down into its leaves.
    """

    strategy: Strategy

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        for child_ref in expr.descendents:
            for replacement in self.strategy(child_ref):
                yield replacement
                return

    def optimize(self, executor, strategy):
        self.strategy.optimize(executor, strategy)


@dataclasses.dataclass
class StrategyRepeat(Strategy):
    """
    Returns a new replacement strategy that repeatedly calls the replacement strategy
    """

    strategy: Strategy
    max_calls: int = 1000

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        i = 0

        for i in range(self.max_calls):
            replaced = False
            for replacement in self.strategy(expr):
                replaced = True
                yield replacement
            if not replaced:
                return
        raise RuntimeError("Exceeded maximum number of repitions")

    def optimize(self, executor, strategy):
        """
        Apply passed in strategy repeatedly.
        """
        self.strategy.optimize(executor, self)

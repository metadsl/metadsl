"""
Pattern matching strategies.

Inspired by this poster
    https://drive.google.com/file/d/10nWoSHGH1ACgdslcnPXwPvEekh9ae9x4/view
and this paper
    Visser et. al.: Building program optimizers with rewriting strategies (ICFP 1998)
"""
from __future__ import annotations

import typing
import dataclasses
from metadsl import *

__all__ = ["Strategy", "Executor", "Result"]

T = typing.TypeVar("T")


def _execute_all(ref: ExpressionReference, strategy: Strategy) -> object:
    """
    Call a replacement strategy many times, returning the last result whole.
    """
    for replacement in strategy(ref):
        pass
    return ref.expression


@dataclasses.dataclass
class Executor:
    # rule that is used if none is passed in
    default_strategy: Strategy
    # Function that takes a rule and an expression and executes it
    execute: typing.Callable[
        [ExpressionReference, Strategy], object
    ] = dataclasses.field(default=_execute_all)

    def __call__(self, expr: T, strategy: typing.Optional[Strategy] = None) -> T:
        execute: typing.Callable[  # type: ignore
            [ExpressionReference, Strategy], object
        ] = self.execute  # type: ignore
        default_strategy: Strategy = self.default_strategy  # type: ignore
        strategy = strategy or default_strategy
        assert strategy
        return typing.cast(
            T,
            execute(
                ExpressionReference.from_expression(clone_expression(expr)), strategy
            ),
        )

    def optimize(self) -> None:
        self.default_strategy.optimize(self, NoOpStrategy())


@dataclasses.dataclass
class Result:
    # The name of the strategy that was executed
    name: str
    # Any optional logs for this strategy
    logs: str = ""
    # An optional label for this replacement
    label: typing.Optional[str] = None


class Strategy(typing.Protocol):
    def __call__(self, ref: ExpressionReference) -> typing.Iterable[Result]:
        ...

    def optimize(self, executor: Executor, strategy: Strategy) -> None:
        """

        """
        ...


class NoOpStrategy(Strategy):
    def __call__(self, ref):
        return tuple()

    def optimize(self, executor, strategy):
        pass

from __future__ import annotations

import typing
import dataclasses
import collections
import functools
import contextlib

from metadsl import *
from .strategies import *
from .combinators import *

__all__ = ["StrategyNormalize", "Registrator"]

T = typing.TypeVar("T")


def add_set(set_: typing.Set[T], item: T) -> T:
    set_.add(item)
    return item


@dataclasses.dataclass
class Registrator:
    """
    Helper class for adding strategies to the StrategyNormalize
    """

    strategy: StrategyNormalize

    def pre(self, strategy: Strategy) -> Strategy:
        self.strategy.pre.add(strategy)
        return strategy

    def post(self, strategy: Strategy) -> Strategy:
        self.strategy.post.add(strategy)
        return strategy

    def __getitem__(self, label: str) -> typing.Callable[[Strategy], Strategy]:
        set_ = self.strategy.phases[label]
        return functools.partial(add_set, set_)  # type: ignore

    def __delitem__(self, label: str) -> None:
        del self.strategy.phases[label]

    def __contains__(self, label: str) -> bool:
        return label in self.strategy.phases

    @contextlib.contextmanager
    def tmp(self, *strategies: Strategy):
        """
        Context manager that temporarily appends a list of strategies
        """
        TMP_NAME = "__tmp"
        for s in strategies:
            self[TMP_NAME](s)
        try:
            yield
        except Exception:
            raise
        finally:
            if TMP_NAME in self:
                del self[TMP_NAME]


@dataclasses.dataclass
class StrategyNormalize(Strategy):
    """
    A strategy combinator that expresses strategies in a number of phases. Each phase can
    execute strategies in all the phases before it. After each phase has no more matches,
    a label is set. This lets you explore when each phase is done executing.
    
    """

    pre: typing.Set[Strategy] = dataclasses.field(default_factory=set)
    post: typing.Set[Strategy] = dataclasses.field(default_factory=set)
    phases: typing.DefaultDict[str, typing.Set[Strategy]] = dataclasses.field(
        default_factory=lambda: collections.defaultdict(set)
    )

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Result]:
        return self.strategy(expr)

    def optimize(self, executor: Executor, strategy: Strategy) -> None:
        self.strategy.optimize(executor, strategy)
        # """
        # pre and post stay the same and the strategies in phases are all updated
        # """
        # assert not strategy
        # new_phases = collections.OrderedDict[str, typing.Set[Strategy]]()
        # for old_phase, strategy in zip(self.phases.items(), self.phase_strategies):
        #     label, old_strategies = old_phase
        #     new_phases[label] = set(
        #         old_strategy.optimize(executor, strategy)
        #         for old_strategy in old_strategies
        #     )
        # return dataclasses.replace(self, phases=new_phases)

    @property
    def pre_strategy(self) -> Strategy:
        return StrategyFold(StrategySequence(*self.pre))

    @property
    def post_strategy(self) -> Strategy:
        return StrategyFold(StrategySequence(*self.post))

    @property
    def phase_strategies(self) -> typing.Tuple[Strategy, ...]:
        current_strategies: typing.Set[Strategy] = set()
        phases: typing.List[Strategy] = []
        for label, strategies in self.phases.items():
            current_strategies.update(strategies)
            phases.append(
                StrategyLabel(
                    label,
                    StrategyRepeat(
                        StrategyInOrder(
                            self.pre_strategy,
                            StrategyFold(StrategySequence(*current_strategies)),
                        ),
                    ),
                )
            )
        return tuple(phases)

    @property
    def strategy(self) -> Strategy:
        return StrategyRepeat(
            StrategyInOrder(
                StrategyLabel("pre", StrategyRepeat(self.pre_strategy)),
                *self.phase_strategies,
                StrategyLabel("post", self.post_strategy)
            )
        )

"""
Replacement rules are allow you to define transformation of expressions.

This file provides a number of functions that allows you to combine rules and apply them
to the whole tree.

This allows you to take a rule that optionally replaces one node and map it throughout the tree
and keep calling it until it no longer matches.
"""

import typing
import dataclasses
from .expressions import *

__all__ = [
    "Rule",
    "NoMatch",
    "RulesRepeatSequence",
    "RulesRepeatFold",
    "RuleSequence",
    "RuleInOrder",
    "RuleFold",
    "RuleRepeat",
]


class NoMatch(Exception):
    pass


# takes in an expression object and returns a new one if it matches, otherwise raises NoMatch
# We type this as `object` instead of `Expression` because  we can pass in a leaf of an expression
# tree which is not an expression object.
Rule = typing.Callable[[object], object]


@dataclasses.dataclass
class RulesRepeatSequence:
    """
    This takes in a list of rules and repeatedly applies them until no more match.
    """

    rules: typing.Tuple[Rule, ...]
    _rule: Rule

    def __init__(self, *rules: Rule):
        self.rules = rules
        self._update_rule()

    def _update_rule(self):
        execute_all = RuleSequence(self.rules)
        execute_many_times = RuleRepeat(execute_all)
        self._rule = execute_many_times

    def __call__(self, expr: object) -> typing.Optional[object]:
        return self._rule(expr)  # type: ignore

    def append(self, rule: Rule) -> Rule:
        self.rules += (rule,)
        self._update_rule()
        return rule


@dataclasses.dataclass(init=False)
class RulesRepeatFold:
    """
    This takes in a list of rules and repeatedly applies them recursively to the
    tree, until no more match anywhere.
    """

    rules: typing.Tuple[Rule, ...]
    _rule: Rule

    def __init__(self, *rules: Rule):
        self.rules = rules
        self._update_rule()

    def _update_rule(self):
        execute_all = RuleSequence(self.rules)
        execute_many_times = RuleRepeat(execute_all)
        execute_fold = RuleFold(execute_many_times)
        execute_fold_many_times = RuleRepeat(execute_fold)
        self._rule = execute_fold_many_times

    def __call__(self, expr: object) -> typing.Optional[object]:
        return self._rule(expr)  # type: ignore

    def append(self, rule: Rule) -> Rule:
        self.rules += (rule,)
        self._update_rule()
        return rule


@dataclasses.dataclass(init=False)
class RuleInOrder:
    """
    Returns a new replacement rule that executes each of the rules in order,
    returning a new expression if any of them replaced.
    """

    rules: typing.Tuple[Rule, ...]

    def __init__(self, *rules: Rule):
        self.rules = rules

    def __call__(self, expr: object) -> typing.Optional[object]:
        did_replace = False
        for rule in self.rules:
            try:
                res = rule(expr)
            except NoMatch:
                pass
            else:
                did_replace = True
                expr = res
        if not did_replace:
            raise NoMatch
        return expr


@dataclasses.dataclass
class RuleSequence:
    """
    Returns a new replacement rule that tries each of the replacement rules in sequence, returning the result of the first that matches.
    """

    rules: typing.Tuple[Rule, ...]

    def __call__(self, expr: object) -> typing.Optional[object]:
        for rule in self.rules:
            try:
                return rule(expr)
            except NoMatch:
                pass
        raise NoMatch


@dataclasses.dataclass
class RuleFold:
    """
    Returns a new replacement rule that calls it on every node of the tree, returning a new expression if any of the nodes were updated
    or None if none of them were.
    """

    rule: Rule
    folder: ExpressionFolder = dataclasses.field(init=False)
    executed_rule: bool = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self.fn)

    def __call__(self, expr: object) -> typing.Optional[object]:
        self.executed_rule = False
        res = self.folder(expr)
        if not self.executed_rule:
            return None
        return res

    def fn(self, value: object) -> object:
        try:
            new_value = self.rule(value)  # type: ignore
        except NoMatch:
            return value
        self.executed_rule = True
        return new_value


@dataclasses.dataclass
class RuleRepeat:
    """
    Returns a new replacement rule that repeatedly calls the replacement rule
    """

    rule: Rule

    def __call__(self, expr: object) -> typing.Optional[object]:
        try:
            expr = self.rule(expr)  # type: ignore
        except NoMatch:
            return expr
        for i in range(1000):
            try:
                expr = self.rule(expr)  # type: ignore
            except NoMatch:
                return expr
        raise RuntimeError(
            f"Exceeded maximum number of repitions, rule: {self.rule}, expr: {expr}"  # type: ignore
        )

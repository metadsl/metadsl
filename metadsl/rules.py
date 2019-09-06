"""
Replacement rules are allow you to define transformation of expressions.

This file provides a number of functions that allows you to combine rules and apply them
to the whole tree.

This allows you to take a rule that optionally replaces one node and map it throughout the tree
and keep calling it until it no longer matches.
"""

from __future__ import annotations

import typing
import dataclasses
from .expressions import *

__all__ = [
    "Rule",
    "execute",
    "RulesRepeatSequence",
    "RulesRepeatFold",
    "RuleSequence",
    "RuleInOrder",
    "RuleFold",
    "RuleRepeat",
    "CollapseReplacementsRule",
]

T = typing.TypeVar("T")


@dataclasses.dataclass
class Replacement(typing.Generic[T]):
    """
    Replacement is a record of a replacement that happened.
    """

    # The name of the rule that was executed
    rule: str
    # The resulting full expression
    result: T
    # An optional label for this replacement
    label: typing.Optional[str] = None


# takes in an expression object and returns a number of replacements executed on the expression
Rule = typing.Callable[[T], typing.Iterable[Replacement[T]]]


@dataclasses.dataclass
class Executor:
    # Function that takes a rule and an expressiona and executes it
    execute: typing.Callable[[T, Rule], T]
    # rule that is used if none is passed in
    default_rule: typing.Optional[Rule]

    def __call__(self, expr: T, rule: typing.Optional[Rule] = None) -> T:
        return self.execute(expr, rule or self.default_rule)  # type: ignore


def _execute_all(expr: T, rule: Rule) -> T:
    """
    Call a replacement rule many times, returning the last result whole.
    """
    for replacement in rule(expr):
        expr = replacement.result
    return expr


# Execute should be called on an expression to get the result
# External modules can set a custom `execute` function or `default_rule`
# to modify the behavior
execute = Executor(_execute_all, None)


T_Rule = typing.TypeVar("T_Rule", bound=Rule)


@dataclasses.dataclass
class CollapseReplacementsRule:
    """
    Takes in an existing rule and gives the last state a label.
    """

    label: str
    rule: Rule

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        last_replacement = None
        for replacement in self.rule(expr):  # type: ignore
            if last_replacement:
                yield last_replacement
            last_replacement = replacement
        if last_replacement:
            yield Replacement(
                rule=last_replacement.rule,
                result=last_replacement.result,
                label=self.label,
            )


@dataclasses.dataclass(init=False)
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

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        return self._rule(expr)  # type: ignore

    def append(self, rule: T_Rule) -> T_Rule:
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
        execute_fold = RuleFold(execute_all)
        execute_fold_many_times = RuleRepeat(execute_fold)
        self._rule = execute_fold_many_times

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        return self._rule(expr)  # type: ignore

    def append(self, rule: T_Rule) -> T_Rule:
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

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        for rule in self.rules:
            for replacement in rule(expr):
                expr = replacement.result
                yield replacement


@dataclasses.dataclass
class RuleSequence:
    """
    Returns a new replacement rule that tries each of the replacement rules in sequence, returning the result of the first that matches.
    """

    rules: typing.Tuple[Rule, ...]

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        for rule in self.rules:
            for replacement in rule(expr):
                yield replacement
                return


def replace_expression_arg(expr: Expression, idx: int, arg: object) -> Expression:
    args = list(expr.args)
    args[idx] = arg
    return dataclasses.replace(expr, args=tuple(args))


def replace_expression_kwarg(expr: Expression, key: str, arg: object) -> Expression:
    kwargs = dict(expr.kwargs)
    kwargs[key] = arg
    return dataclasses.replace(expr, kwargs=kwargs)


@dataclasses.dataclass
class RuleFold:
    """
    Returns the first replacement found by starting at the top of the expression tree
    and then recursing down into its leaves.
    """

    rule: Rule

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        replacement: typing.Optional[Replacement] = None
        # First lets try calling the replacement rule on the top level
        for replacement in self.rule(expr):  # type: ignore
            yield replacement
            # If we found a replacement there, we are all good, we can exit
            return

        if not isinstance(expr, Expression):
            return

        # Next, let's go through each arg and see if we can replace it
        for i, arg in enumerate(expr.args):
            for replacement in self(arg):
                yield dataclasses.replace(
                    replacement,
                    result=replace_expression_arg(expr, i, replacement.result),
                )
                return

        # Now we can do the same for the kwargs
        for key, arg in expr.kwargs.items():
            for replacement in self(arg):
                yield dataclasses.replace(
                    replacement,
                    result=replace_expression_kwarg(expr, key, replacement.result),
                )
                return


@dataclasses.dataclass
class RuleRepeat:
    """
    Returns a new replacement rule that repeatedly calls the replacement rule
    """

    rule: Rule
    max_calls: int = 1000

    def __call__(self, expr: object) -> typing.Iterable[Replacement]:
        i = 0

        for i in range(self.max_calls):
            replaced = False
            for replacement in self.rule(expr):  # type: ignore
                replaced = True
                yield replacement
            if not replaced:
                return
            expr = replacement.result
        raise RuntimeError(
            f"Exceeded maximum number of repitions, rule: {self.rule}, expr: {expr}"  # type: ignore
        )

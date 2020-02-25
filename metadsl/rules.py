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
from .normalized import *

__all__ = [
    "Rule",
    "execute",
    "RulesRepeatSequence",
    "RulesRepeatFold",
    "RulesSequenceFold",
    "RuleSequence",
    "RuleInOrder",
    "RuleFold",
    "RuleRepeat",
    "Replacement",
    "CollapseReplacementsRule",
]
T = typing.TypeVar("T")


@dataclasses.dataclass
class Replacement:
    """
    Replacement is a record of a replacement that happened.
    """

    # The name of the rule that was executed
    rule: str
    # An optional label for this replacement
    label: typing.Optional[str] = None


# takes in an expression object and returns a number of replacements executed on the expression
Rule = typing.Callable[[ExpressionReference], typing.Iterable[Replacement]]


@dataclasses.dataclass
class Executor:
    # Function that takes a rule and an expression and executes it
    execute: typing.Callable[[ExpressionReference, Rule], object]
    # rule that is used if none is passed in
    default_rule: Rule

    def __call__(self, expr: T, rule: typing.Optional[Rule] = None) -> T:
        execute: typing.Callable[  # type: ignore
            [ExpressionReference, Rule], object
        ] = self.execute  # type: ignore
        default_rule: Rule = self.default_rule  # type: ignore
        rule = rule or default_rule
        assert rule
        return typing.cast(
            T,
            execute(
                ExpressionReference.from_expression(ExpressionFolder()(expr)), rule
            ),
        )


def _execute_all(ref: ExpressionReference, rule: Rule) -> object:
    """
    Call a replacement rule many times, returning the last result whole.
    """
    for replacement in rule(ref):
        pass
    return ref.expression


# Execute should be called on an expression to get the result
# External modules can set a custom `execute` function or `default_rule`
# to modify the behavior
execute = Executor(_execute_all, lambda e: [])


T_Rule = typing.TypeVar("T_Rule", bound=Rule)


@dataclasses.dataclass
class CollapseReplacementsRule:
    """
    Takes in an existing rule and adds a final state with a custom label.
    """

    label: str
    rule: Rule

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        replacement = None
        for replacement in self.rule(expr):  # type: ignore
            yield replacement
        if replacement:
            yield Replacement(rule="", label=self.label)


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
        self._rule = execute_many_times  # type: ignore

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        rule: Rule = self._rule  # type: ignore
        return rule(expr)

    def append(self, rule: T_Rule) -> T_Rule:
        self.rules += (rule,)
        self._update_rule()
        return rule


@dataclasses.dataclass(init=False)
class RulesSequenceFold:

    rules: typing.Tuple[Rule, ...]
    _rule: Rule

    def __init__(self, *rules: Rule):
        self.rules = rules
        self._update_rule()

    def _update_rule(self):
        execute_all = RuleSequence(self.rules)
        execute_fold = RuleFold(execute_all)
        self._rule = execute_fold  # type: ignore

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        rule: Rule = self._rule  # type: ignore
        return rule(expr)

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
        self._rule = execute_fold_many_times  # type: ignore

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        rule: Rule = self._rule  # type: ignore
        return rule(expr)

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

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        for rule in self.rules:
            for replacement in rule(expr):
                yield replacement


@dataclasses.dataclass
class RuleSequence:
    """
    Returns a new replacement rule that tries each of the replacement rules in sequence, returning the result of the first that matches.
    """

    rules: typing.Tuple[Rule, ...]

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        for rule in self.rules:
            replacement = None
            for replacement in rule(expr):
                yield replacement
            if replacement:
                return


@dataclasses.dataclass
class RuleFold:
    """
    Returns the first replacement found by starting at the top of the expression tree
    and then recursing down into its leaves.
    """

    rule: Rule

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        rule: Rule = self.rule  # type: ignore
        for child_ref in expr.descendents:
            for replacement in rule(child_ref):
                yield replacement
                return


@dataclasses.dataclass
class RuleRepeat:
    """
    Returns a new replacement rule that repeatedly calls the replacement rule
    """

    _rule: Rule
    max_calls: int = 1000

    def __call__(self, expr: ExpressionReference) -> typing.Iterable[Replacement]:
        i = 0
        rule: Rule = self._rule  # type: ignore

        for i in range(self.max_calls):
            replaced = False
            for replacement in rule(expr):
                replaced = True
                yield replacement
            if not replaced:
                return
        raise RuntimeError(
            f"Exceeded maximum number of repitions, rule: {rule}, expr: {expr}"  # type: ignore
        )

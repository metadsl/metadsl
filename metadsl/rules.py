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

__all__ = ["Rule", "rule_sequence", "rule_fold", "rule_repeat"]
Rule = typing.Callable[[ExpressionType], typing.Optional[ExpressionType]]


@dataclasses.dataclass
class RuleSequence:
    rules: typing.List[Rule]

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        res = None
        for rule in self.rules:
            res = rule(expr)
            if res is not None:
                return res
        return res


def rule_sequence(*rules) -> Rule:
    """
    Returns a new replacement rule that tries each of the replacement rules in sequence, returning the result of the first that matches.
    """
    return RuleSequence(list(rules))


Intermediate = typing.Tuple[bool, object]


@dataclasses.dataclass
class RuleFold:
    rule: Rule
    folder: ExpressionFolder = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self._value_fn, self._call_fn)

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        # Folds over the expression, at each step returning a tuple of (matched, value)
        # where matched is a boolean if any rules have matched yet and value is the replaced value
        matched, res = self.folder(expr)
        if not matched:
            return None
        return typing.cast(ExpressionType, res)

    def _value_fn(self, value: object) -> Intermediate:
        new_value = self.rule(value)  # type: ignore
        if new_value is None:
            return (False, value)
        return (True, new_value)

    def _call_fn(
        self, fn: typing.Callable, args: typing.Tuple[Intermediate, ...]
    ) -> Intermediate:
        new_args: typing.List[ExpressionType] = []
        any_matched = False
        # This call matched if any of it's args had matched.
        for (matched, arg) in args:
            any_matched = any_matched or matched
            new_args.append(typing.cast(ExpressionType, arg))
        call = RecursiveCall(fn, tuple(new_args))
        new_call = self.rule(call)  # type: ignore
        if new_call is None:
            return (any_matched, call)
        return (True, new_call)


def rule_fold(rule: Rule) -> Rule:
    """
    Returns a new replacement rule that calls it on every node of the tree, returning a new expression if any of the nodes were updated
    or None if none of them were.
    """
    return RuleFold(rule)


@dataclasses.dataclass
class RuleRepeat:
    rule: Rule

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        replaced = self.rule(expr)  # type: ignore
        if replaced is None:
            return None
        expr = replaced
        for i in range(1000):
            replaced = self.rule(expr)  # type: ignore
            if replaced is None:
                return expr
            expr = replaced
        raise RuntimeError(
            f"Exceeded maximum number of repitions, rule: {self.rule}, expr: {expr}"  # type: ignore
        )


def rule_repeat(rule: Rule) -> Rule:
    """
    Returns a new replacement rule that repeatedly calls the replacement rule
    """
    return RuleRepeat(rule)

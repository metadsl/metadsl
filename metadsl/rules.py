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
    "RulesRepeatSequence",
    "RulesRepeatFold",
    "RuleSequence",
    "RuleInOrder",
    "RuleFold",
    "RuleRepeat",
]

# takes in an expression object and returns a new one if it matches, otherwise returns None
# We type this as `object` instead of `Expression` because  we can pass in a leaf of an expression
# tree which is not an expression object.
Rule = typing.Callable[[object], typing.Optional[object]]


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
            res = rule(expr)
            if res is not None:
                did_replace = True
                expr = res
        return expr if did_replace else None


@dataclasses.dataclass
class RuleSequence:
    """
    Returns a new replacement rule that tries each of the replacement rules in sequence, returning the result of the first that matches.
    """

    rules: typing.Tuple[Rule, ...]

    def __call__(self, expr: object) -> typing.Optional[object]:
        res = None
        for rule in self.rules:
            res = rule(expr)
            if res is not None:
                return res
        return res


# we fold up the expression tree, maintaining the current expression
Intermediate = typing.Tuple[bool, object]


@dataclasses.dataclass
class RuleFold:
    """
    Returns a new replacement rule that calls it on every node of the tree, returning a new expression if any of the nodes were updated
    or None if none of them were.
    """

    rule: Rule
    folder: ExpressionFolder = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self._value_fn, self._expression_fn)

    def __call__(self, expr: object) -> typing.Optional[object]:
        # Folds over the expression, at each step returning a tuple of (matched, value)
        # where matched is a boolean if any rules have matched yet and value is the replaced value
        matched, res = self.folder(expr)
        if not matched:
            return None
        return res

    def _value_fn(self, value: object) -> Intermediate:
        new_value = self.rule(value)  # type: ignore
        if new_value is None:
            return (False, value)
        return (True, new_value)

    def _expression_fn(
        self,
        type: typing.Type[Expression],
        fn: typing.Callable,
        args: typing.Tuple[Intermediate, ...],
    ) -> Intermediate:
        new_args: typing.List[object] = []
        any_matched = False
        # This call matched if any of it's args had matched.
        for (matched, arg) in args:
            any_matched = any_matched or matched
            new_args.append(arg)
        expr = type(fn, tuple(new_args))
        new_expr = self.rule(expr)  # type: ignore
        if new_expr is None:
            return (any_matched, expr)
        return (True, new_expr)


@dataclasses.dataclass
class RuleRepeat:
    """
    Returns a new replacement rule that repeatedly calls the replacement rule
    """

    rule: Rule

    def __call__(self, expr: object) -> typing.Optional[object]:
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

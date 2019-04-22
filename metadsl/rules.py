"""
Replacement rules are allow you to define transformation of expressions.

This file provides a number of functions that allows you to combine rules and apply them
to the whole tree.

This allows you to take a rule that optionally replaces one node and map it throughout the tree
and keep calling it until it no longer matches.
"""

import typing
import dataclasses
from .expressions import Expression, Call

__all__ = ["Rule", "rule_sequence", "rule_fold", "rule_repeat"]
Rule = typing.Callable[[Expression], typing.Optional[Expression]]


@dataclasses.dataclass
class RuleSequence:
    rules: typing.List[Rule]

    def __call__(self, expr: Expression) -> typing.Optional[Expression]:
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

    def __call__(self, expr: Expression) -> typing.Optional[Expression]:
        # Folds over the expression, at each step returning a tuple of (matched, value)
        # where matched is a boolean if any rules have matched yet and value is the replaced value
        matched, res = expr.fold(
            self._expr_fn,
            self._call_value_fn,
            self._other_value_fn,
            self._other_value_fn,
        )
        if not matched:
            return None
        return typing.cast(Expression, res)

    def _expr_fn(self, expr: Expression[typing.Any, Intermediate]) -> Intermediate:
        matched, value = expr.value
        new_expr = expr.replace_value(value)
        replaced_expr = self.rule(new_expr)  # type: ignore
        if replaced_expr is None:
            return (matched, new_expr)
        return (True, replaced_expr)

    def _call_value_fn(self, call: Call[Intermediate]) -> Intermediate:
        args: typing.List[Expression] = []
        any_matched = False
        # This call matched if any of it's args had matched.
        for (matched, arg) in call.args:
            any_matched = any_matched or matched
            args.append(typing.cast(Expression, arg))
        return (any_matched, call.replace_args(*args))

    def _other_value_fn(self, value: object) -> Intermediate:
        return (False, value)


def rule_fold(rule: Rule) -> Rule:
    """
    Returns a new replacement rule that calls it on every node of the tree, returning a new expression if any of the nodes were updated
    or None if none of them were.
    """
    return RuleFold(rule)


@dataclasses.dataclass
class RuleRepeat:
    rule: Rule

    def __call__(self, expr: Expression) -> typing.Optional[Expression]:
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

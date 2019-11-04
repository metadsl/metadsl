"""
We have a set of core rules that we want to execute all the time.

We also have a number of named rules, for conversions.
"""

import collections
import typing

from metadsl import *

__all__ = [
    "register",
    "register_convert",
    "register_unbox",
    "register_numpy_engine",
    "register_post",
    "register_pre",
    "register_optimize",
    "run_post_rules",
    "rule_groups",
    "all_rules",
]


core_rules = RulesRepeatFold()
register = core_rules.append


# Rules that have to take place before any other rules
core_pre_rules = RulesRepeatFold()
register_pre = core_pre_rules.append

# Rules that have to take place only after all other rules
core_post_rules = RulesSequenceFold()
register_post = core_post_rules.append


# Conversions from untyped values to typed values
convert_rules = RulesRepeatFold()
register_convert = convert_rules.append


unbox_rules = RulesRepeatFold()
register_unbox = unbox_rules.append


numpy_engine = RulesRepeatFold()
register_numpy_engine = numpy_engine.append

optimize_rules = RulesRepeatFold()
register_optimize = optimize_rules.append


rule_groups: typing.DefaultDict[str, Rule] = collections.defaultdict(
    core=core_rules,
    convert=convert_rules,
    optimize=optimize_rules,
    unbox=unbox_rules,
    execute=numpy_engine,
)

RUN_POST_RULES = True


def run_post_rules(should_run: bool) -> None:
    global RUN_POST_RULES
    RUN_POST_RULES = should_run


def all_rules(expression: ExpressionReference) -> typing.Iterable[Replacement]:
    sub_rules: typing.List[Rule] = [core_pre_rules]
    rules_in_order: typing.List[Rule] = []
    for k, v in rule_groups.items():
        sub_rules.append(v)
        rules_in_order.append(
            CollapseReplacementsRule(k, RulesRepeatSequence(*sub_rules))
        )
    ordered = RuleInOrder(*rules_in_order)
    if RUN_POST_RULES:
        return RulesRepeatSequence(ordered, core_post_rules)(expression)
    return ordered(expression)


execute.default_rule = all_rules  # type: ignore


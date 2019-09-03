"""
We have a set of core rules that we want to execute all the time.

We also have a number of named rules, for conversions.
"""

from metadsl import *

__all__ = [
    "register",
    "register_convert",
    "register_unbox",
    "register_numpy_engine",
    "register_post",
    "execute_core",
    "all_rules",
]


core_rules = RulesRepeatFold()
register = core_rules.append

# Rules that have to take place only after all other rules
core_post_rules = RulesRepeatFold()
register_post = core_post_rules.append


# Conversions from untyped values to typed values
convert_rules = RulesRepeatFold()
register_convert = convert_rules.append


unbox_rules = RulesRepeatFold()
register_unbox = unbox_rules.append


numpy_engine = RulesRepeatFold()
register_numpy_engine = numpy_engine.append


all_rules = RuleInOrder(
    CollapseReplacementsRule("core", RulesRepeatSequence(core_rules)),
    CollapseReplacementsRule("convert", RulesRepeatSequence(core_rules, convert_rules)),
    CollapseReplacementsRule(
        "unbox", RulesRepeatSequence(core_rules, convert_rules, unbox_rules)
    ),
    CollapseReplacementsRule(
        "execute",
        RulesRepeatSequence(core_rules, convert_rules, numpy_engine, core_post_rules),
    ),
)

execute_core = lambda e: execute_rule(all_rules, e)


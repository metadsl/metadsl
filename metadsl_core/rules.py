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
    "register_pre",
    "run_post_rules",
    "register_optimize",
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

all_rules = RuleInOrder(
    CollapseReplacementsRule("core", RulesRepeatSequence(core_pre_rules, core_rules)),
    CollapseReplacementsRule(
        "convert", RulesRepeatSequence(core_pre_rules, core_rules, convert_rules)
    ),
    CollapseReplacementsRule(
        "optimize",
        RulesRepeatSequence(core_pre_rules, core_rules, convert_rules, optimize_rules),
    ),
    CollapseReplacementsRule(
        "unbox",
        RulesRepeatSequence(
            core_pre_rules, core_rules, convert_rules, optimize_rules, unbox_rules
        ),
    ),
    CollapseReplacementsRule(
        "execute",
        RulesRepeatSequence(
            core_pre_rules,
            core_rules,
            convert_rules,
            optimize_rules,
            unbox_rules,
            numpy_engine,
        ),
    ),
)


def run_post_rules(should_run: bool) -> None:
    # Set to use core rules by default
    execute.default_rule = (  # type: ignore
        RulesRepeatSequence(all_rules, core_post_rules) if should_run else all_rules
    )


run_post_rules(True)

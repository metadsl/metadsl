from metadsl import *

__all__ = ["core_rules", "register", "execute_core"]


core_rules = RulesRepeatFold()
register = core_rules.append
execute_core = lambda e: execute_rule(core_rules, e)

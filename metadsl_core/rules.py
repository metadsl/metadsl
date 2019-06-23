from metadsl import RulesRepeatFold

__all__ = ["core_rules", "register"]


core_rules = RulesRepeatFold()
register = core_rules.append

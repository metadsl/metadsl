from metadsl import *
from metadsl_core import *

__all__ = [
    "register_llvmlite_ir_ref",
    "register_llvmlite_ir",
    "register_llvmlite_binding",
    "register_ctypes",
]

llvmlite_ir_ref_rules = RulesRepeatFold()
register_llvmlite_ir_ref = llvmlite_ir_ref_rules.append
rule_groups["llvmlite.ir (reference)"] = llvmlite_ir_ref_rules


llvmlite_ir_rules = RulesRepeatFold()
register_llvmlite_ir = llvmlite_ir_rules.append
rule_groups["llvmlite.ir"] = llvmlite_ir_rules


llvmlite_binding_rules = RulesRepeatFold()
register_llvmlite_binding = llvmlite_binding_rules.append
rule_groups["llvmlite.binding"] = llvmlite_binding_rules


ctypes_rules = RulesRepeatFold()
register_ctypes = ctypes_rules.append
rule_groups["ctypes"] = ctypes_rules

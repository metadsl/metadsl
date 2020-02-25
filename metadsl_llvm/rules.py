import typing
from metadsl_core import rule_groups

from .ctypes import ctypes_rules
from .integration import llvm_integration_rules
from .ir_llvmlite import ir_llvmlite_rules
from .llvmlite_binding import llvmlite_binding_rules
from .ir_context import ir_context_rules

__all__: typing.List[str] = []


# First do higher level context rules
rule_groups["llvmlite.context"] = ir_context_rules
# First do integration rules so that all functions are created
rule_groups["llvmlite.integration"] = llvm_integration_rules
# Then create the llvm modules
rule_groups["llvmlite.ir_llvmlite"] = ir_llvmlite_rules
# Finally you can create the ctypes
rule_groups["llvmlite.ctypes"] = ctypes_rules
# And then compile into a function
rule_groups["llvmlite.llvmlite_binding"] = llvmlite_binding_rules

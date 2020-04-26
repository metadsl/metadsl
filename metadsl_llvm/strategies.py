from metadsl_rewrite import *

__all__ = [
    "register_context",
    "register_integration",
    "register_llvmlite",
    "register_ctypes",
    "register_llvmlite_binding",
]

# First do higher level context rules
register_context = register["llvmlite.context"]
# First do integration rules so that all functions are created
register_integration = register["llvmlite.integration"]
# Then create the llvm modules
register_llvmlite = register["llvmlite.ir_llvmlite"]
#  Finally you can create the ctypes
register_ctypes = register["llvmlite.ctypes"]
# And then compile into a function
register_llvmlite_binding = register["llvmlite.llvmlite_binding"]

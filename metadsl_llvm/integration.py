from __future__ import annotations
import typing
import ctypes


from metadsl import *
from metadsl_core import *
from .ir import *
from .ctypes import *
from .llvmlite_binding import *
from .ir_llvmlite import *

__all__ = ["llvm_integration_rules", "make_c_wrapper", "compile_function"]


llvm_integration_rules = RulesRepeatFold()
register_integration = llvm_integration_rules.append


@expression
def concat_strings(l: str, r: str) -> str:
    return l + r


register(default_rule(concat_strings))


def make_c_wrapper(mod_ref: ModRef, original_fn_ref: FnRef) -> typing.Tuple[str, Fn]:
    """
    Creates a new function that wraps the old function,
    making sure the calling convention is default.
    """
    new_name = concat_strings("entry_", original_fn_ref.name)
    fn_ref = mod_ref.fn(new_name, original_fn_ref.type,)
    block_ref = fn_ref.block(True, "entry")
    return (
        new_name,
        fn_ref.fn(block_ref.ret(block_ref.call(original_fn_ref, fn_ref.arguments))),
    )


@expression
def compile_function(
    mod: Mod, fn_ref: FnRef, cfunctype: CFunctionType, optimization: int = 1,
) -> typing.Callable:
    new_name, wrapper_fn = make_c_wrapper(mod.ref, fn_ref)
    module_ref = ModuleRef.create(mod_str(mod.add_fn(wrapper_fn)))
    module_ref = module_ref.optimize(optimization)
    engine = ExecutionEngine.create(module_ref)
    return cfunctype(engine.get_function_address(new_name))


register_integration(default_rule(compile_function))

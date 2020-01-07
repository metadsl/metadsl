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


@expression
def make_c_wrapper(mod_ref: ModRef, original_fn_ref: FnRef) -> typing.Tuple[str, Fn]:
    """
    Creates a new function that wraps the old function,
    making sure the calling convention is default.
    """
    new_name = concat_strings("entry_", original_fn_ref.name)
    fn_ref = mod_ref.function_(new_name, original_fn_ref.type,)
    block_ref = fn_ref.block(True, "entry")
    return (
        new_name,
        Fn.create(
            Vec.create(block_ref.ret(block_ref.call(original_fn_ref, fn_ref.arguments)))
        ),
    )


register_integration(default_rule(make_c_wrapper))


@expression
def compile_function(
    mod: Mod,
    mod_ref: ModRef,
    fn_ref: FnRef,
    cfunctype: CFunctionType,
    optimization: int = 1,
) -> typing.Callable:
    new_name, wrapper_fn = make_c_wrapper(mod_ref, fn_ref)
    engine = ExecutionEngine.create(
        ModuleRef.create(
            mod_str(Mod.create(mod.functions.append(wrapper_fn)))
        ).optimize(optimization)
    )
    return cfunctype(engine.get_function_address(new_name))


register_integration(default_rule(compile_function))

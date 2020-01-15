from __future__ import annotations
import typing
import ctypes


from metadsl import *
from metadsl_core import *
from .ir import *
from .ctypes import *
from .llvmlite_binding import *
from .ir_llvmlite import *

__all__ = ["llvm_integration_rules", "compile_function", "compile_functions"]


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
def llvm_to_c_fn_type(fn_tp: FnType) -> CFunctionType:
    ...


@expression
def llvm_to_c_type(tp: Type) -> CType:
    ...


@register_integration
@rule
def llvm_to_c_fn_type_rule(ret_tp: Type, arg_tps: typing.Sequence[Type]):
    return (
        llvm_to_c_fn_type(FnType.create(ret_tp, *arg_tps)),
        CFunctionType.create(llvm_to_c_type(ret_tp), *(map(llvm_to_c_type, arg_tps))),
    )


@register_integration
@rule
def llvm_to_c_fn_int():
    return (llvm_to_c_type(Type.create_int(32)), CType.c_int())


@expression
def compile_function(
    mod: Mod, fn_ref: FnRef, optimization: int = 1,
) -> typing.Callable:
    new_name, wrapper_fn = make_c_wrapper(mod.ref, fn_ref)
    module_ref = ModuleRef.create(mod_str(mod.add_fn(wrapper_fn)))
    module_ref = module_ref.optimize(optimization)
    engine = ExecutionEngine.create(module_ref)
    return llvm_to_c_fn_type(fn_ref.type)(engine.get_function_address(new_name))


def compile_functions(
    mod_ref: ModRef, fn: Fn, *fns: Fn, optimization: int = 1,
) -> typing.Callable:
    mod = mod_ref.mod(fn, *fns)
    return compile_function(mod, fn.ref)


register_integration(default_rule(compile_function))

from __future__ import annotations
import typing
import ctypes


from metadsl import *
from metadsl_core import *
from .llvmlite_binding import *
from .llvmlite_ir import *
from .rules import register_ctypes


__all__ = ["CType", "CFunctionType", "make_c_wrapper", "compile_function"]


class CType(Expression):
    @expression
    @classmethod
    def c_int(cls) -> CType:
        ...

    @expression
    @classmethod
    def box(cls, tp: typing.Any) -> CType:
        ...


@register_ctypes
@rule
def ctype_cint() -> R[CType]:
    return CType.c_int(), lambda: CType.box(ctypes.c_int)


class CFunctionType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: CType, *args: CType) -> CFunctionType:
        ...

    # Cannot represent type of C function
    @expression
    @classmethod
    def box(cls, tp: typing.Any) -> CFunctionType:
        ...

    @expression
    def __call__(self, ptr: int) -> typing.Callable:
        ...


@register_ctypes
@rule
def c_function_type_create_1(
    return_tp: typing.Any, arg1: typing.Any
) -> R[CFunctionType]:
    return (
        CFunctionType.create(CType.box(return_tp), CType.box(arg1)),
        lambda: CFunctionType.box(ctypes.CFUNCTYPE(return_tp, arg1)),
    )


@register_ctypes
@rule
def cfunc_call(fntype: typing.Any, ptr: int) -> R[typing.Callable]:
    return CFunctionType.box(fntype)(ptr), lambda: fntype(ptr)


@expression
def concat_strings(l: str, r: str) -> str:
    return l + r


register(default_rule(concat_strings))


@expression
def make_c_wrapper(
    module_builder: ModuleBuilder, original_fn_ref: FunctionReference
) -> Pair[ModuleBuilder, Function]:
    """
    Creates a new function that wraps the old function,
    making sure the calling convention is default.
    """
    module_builder, fn_ref = FunctionReference.create(
        module_builder,
        original_fn_ref.type,
        concat_strings("entry_", original_fn_ref.name),
    ).spread
    fn_builder = FunctionBuilder.create(fn_ref)
    fn_builder, block_ref = BlockReference.create("entry", fn_builder).spread
    block_builder = BlockBuilder.create(block_ref)
    block_builder, value = block_builder.call(
        original_fn_ref, fn_builder.arguments
    ).spread
    block_builder = block_builder.ret(value)
    block = Block.create(block_ref, block_builder)
    function = Function.create(fn_ref, Vec.create(block))
    return Pair.create(module_builder, function)


register(default_rule(make_c_wrapper))


@expression
def compile_function(
    module: Module,
    module_builder: ModuleBuilder,
    function_ref: FunctionReference,
    cfunctype: CFunctionType,
    optimization: int = 1,
) -> typing.Callable:
    module_builder, wrapper_fn = make_c_wrapper(module_builder, function_ref).spread
    module = Module.create(module.reference, module.functions.append(wrapper_fn))
    module_ref = ModuleRef.create(module.to_string())
    module_ref = module_ref.optimize(optimization)
    engine = ExecutionEngine.create(module_ref)
    return cfunctype(engine.get_function_address(wrapper_fn.reference.name))


register(default_rule(compile_function))

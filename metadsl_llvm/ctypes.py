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
    module_builder: ModuleBuilder, original_fn_builder: FunctionBuilder
) -> Pair[ModuleBuilder, Function]:
    """
    Creates a new function that wraps the old function,
    making sure the calling convention is default.
    """
    module_builder, fn_builder = FunctionBuilder.create(
        module_builder,
        original_fn_builder.type,
        concat_strings("entry_", original_fn_builder.name),
    ).spread
    fn_builder, block_builder = BlockBuilder.create("entry", fn_builder).spread
    block_builder, value = block_builder.call(
        original_fn_builder, fn_builder.arguments
    ).spread
    block_builder = block_builder.ret(value)
    function = Function.create(fn_builder, Vec.create(block_builder))
    return Pair.create(module_builder, function)


register(default_rule(make_c_wrapper))


@expression
def compile_function(
    module: Module,
    function_builder: FunctionBuilder,
    cfunctype: CFunctionType,
    optimization: int = 1,
) -> typing.Callable:
    module_builder, wrapper_fn = make_c_wrapper(module_builder, function_builder).spread
    module = module.append_function(wrapper_fn)
    module_ref = ModuleRef.create(module.to_string())
    module_ref = module_ref.optimize(optimization)
    engine = ExecutionEngine.create(module_ref)
    return cfunctype(engine.get_function_address(wrapper_fn.builder.name))


register(default_rule(compile_function))

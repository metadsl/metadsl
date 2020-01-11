"""
Generate LLVM IR
"""

# TODO: What if repr of value changes over time like for IR?

from __future__ import annotations
import typing

import llvmlite.ir as ir

from metadsl import *
from metadsl_core import *
from .ir import *

__all__ = ["ir_llvmlite_rules", "mod_str"]

ir_llvmlite_rules = RulesRepeatFold()
register_llvmlite = ir_llvmlite_rules.append


@hash_value.register
def hash_llvmlite_type(value: ir.Type) -> int:
    """
    Add custom hash for LLVM types, because otherwise they all hash to the same.
    """
    return hash((type(value), value._to_string()))


@hash_value.register
def hash_llvmlite_module(mod: ir.Module) -> int:
    """
    Add custom hash to also take into account contents.
    """
    return hash((mod, str(mod)))


@hash_value.register
def hash_llvmlite_function(fn: ir.Function) -> int:
    return hash((fn, str(fn)))


@hash_value.register
def hash_llvmlite_builder(builder: ir.IRBuilder) -> int:
    return hash((builder, str(builder)))


def union_types(type: ir.Type, *types: ir.Type) -> ir.Type:
    for tp in types:
        if tp != type:
            raise NotImplementedError(f"Cannot merge types {tp} and {type}")
    return type


# Overwrite ir builder str representation
ir.IRBuilder.__str__ = lambda self: f"IRBuilder: {hex(id(self))}\n{self.block}"


@expression
def mod_str(mod: Mod) -> str:
    ...


@expression
def box_mod(mod: ir.Module) -> Mod:
    ...


@expression
def box_fn(fn: ir.Function) -> Fn:
    ...


@expression
def box_terminate(builder: ir.IRBuilder) -> Terminate:
    ...


@expression
def box_value(value: ir.Value) -> Value:
    ...


@expression
def box_block_ref(builder: ir.IRBuilder) -> BlockRef:
    ...


@expression
def box_fn_ref(fn: ir.Function) -> FnRef:
    ...


@expression
def box_mod_ref(fn: ir.Module) -> ModRef:
    ...


@expression
def box_fn_type(fn_tp: ir.FunctionType) -> FnType:
    ...


@expression
def box_type(tp: ir.Type) -> Type:
    ...


@register_llvmlite
@rule
def type_create_int_box(bits: int):
    return Type.create_int(bits), lambda: box_type(ir.IntType(bits))


@register_llvmlite
@rule
def function_type_box_1(ret: ir.Type, arg1: ir.Type) -> R[FnType]:
    return (
        FnType.create(box_type(ret), box_type(arg1)),
        lambda: box_fn_type(ir.FunctionType(ret, (arg1,))),
    )


@register_llvmlite
@rule
def function_type_box_2(ret: ir.Type, arg1: ir.Type, arg2: ir.Type) -> R[FnType]:
    return (
        FnType.create(box_type(ret), box_type(arg1), box_type(arg2)),
        lambda: box_fn_type(ir.FunctionType(ret, (arg1, arg2))),
    )


@register_llvmlite
@rule
def function_type_box_3(
    ret: ir.Type, arg1: ir.Type, arg2: ir.Type, arg3: ir.Type
) -> R[FnType]:
    return (
        FnType.create(box_type(ret), box_type(arg1), box_type(arg2), box_type(arg3)),
        lambda: box_fn_type(ir.FunctionType(ret, (arg1, arg2, arg3))),
    )


@register_llvmlite
@rule
def box_mod_ref_create(name: str):
    return ModRef.create(name), lambda: box_mod_ref(ir.Module(name))


@register_llvmlite
@rule
def box_fn_ref_create(
    mod: ir.Module, fn_tp: ir.FunctionType, name: str, calling_convention: str
):
    def inner() -> FnRef:
        fn = ir.Function(mod, fn_tp, name)
        fn.calling_convention = calling_convention
        return box_fn_ref(fn)

    return (
        box_mod_ref(mod).fn(name, box_fn_type(fn_tp), calling_convention),
        inner,
    )


@register_llvmlite
@rule
def fn_ref_arguments(fn: ir.Function):
    return (
        box_fn_ref(fn).arguments,
        lambda: Vec.create(*(box_value(a) for a in fn.args)),
    )


@register_llvmlite
@rule
def block_ref_create(
    is_first: bool, fn: ir.Function, name: typing.Union[str, None], _: _Uniq,
):
    def inner() -> BlockRef:
        # If this is not the first block, make sure the first has already been appeneded
        if not is_first and not fn.blocks:
            raise NoMatch()
        return box_block_ref(ir.IRBuilder(fn.append_basic_block(name or "")))

    return (box_fn_ref(fn)._block(is_first, name, _), inner)


@register_llvmlite
@rule
def block_ref_ret(builder: ir.IRBuilder, value: ir.Value):
    def inner() -> Terminate:
        builder.ret(value)
        return box_terminate(builder)

    return box_block_ref(builder).ret(box_value(value)), inner


@register_llvmlite
@rule
def block_ref_icmp_signed(
    builder: ir.IRBuilder, operator: str, l: ir.Value, r: ir.Value
):
    return (
        box_block_ref(builder).icmp_signed(operator, box_value(l), box_value(r)),
        lambda: box_value(builder.icmp_signed(operator, l, r)),
    )


@register_llvmlite
@rule
def block_ref_call_1(builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value):
    return (
        box_block_ref(builder).call(box_fn_ref(function), Vec.create(box_value(arg1))),
        lambda: box_value(builder.call(function, (arg1,))),
    )


@register_llvmlite
@rule
def block_ref_call_2(
    builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value, arg2: ir.Value
):
    return (
        box_block_ref(builder).call(
            box_fn_ref(function), Vec.create(box_value(arg1), box_value(arg2)),
        ),
        lambda: box_value(builder.call(function, (arg1, arg2))),
    )


@register_llvmlite
@rule
def block_ref_call_3(
    builder: ir.IRBuilder,
    function: ir.Function,
    arg1: ir.Value,
    arg2: ir.Value,
    arg3: ir.Value,
):
    return (
        box_block_ref(builder).call(
            box_fn_ref(function),
            Vec.create(box_value(arg1), box_value(arg2), box_value(arg3)),
        ),
        lambda: box_value(builder.call(function, (arg1, arg2, arg3))),
    )


@register_llvmlite
@rule
def builder_cbranch(
    builder: ir.IRBuilder, cond: ir.Value, true: ir.IRBuilder, false: ir.IRBuilder
):
    def inner() -> Terminate:
        builder.cbranch(cond, true.block, false.block)
        return box_terminate(builder)

    return (
        box_block_ref(builder).cbranch(
            box_value(cond), box_block_ref(true), box_block_ref(false)
        ),
        inner,
    )


@register_llvmlite
@rule
def builder_branch(builder: ir.IRBuilder, target: ir.IRBuilder):
    def inner() -> Terminate:
        builder.branch(target)
        return box_terminate(builder)

    return (
        box_block_ref(builder).branch(box_block_ref(target)),
        inner,
    )


@register_llvmlite
@rule
def builder_add(builder: ir.IRBuilder, left: ir.Value, right: ir.Value):
    builder_ = box_block_ref(builder)
    return (
        builder_.add(box_value(left), box_value(right)),
        lambda: box_value(builder.add(left, right)),
    )


@register_llvmlite
@rule
def builder_sub(builder: ir.IRBuilder, left: ir.Value, right: ir.Value):
    builder_ = box_block_ref(builder)
    return (
        builder_.sub(box_value(left), box_value(right)),
        lambda: box_value(builder.sub(left, right)),
    )


@register_llvmlite
@rule
def builder_phi_two(
    builder: ir.IRBuilder,
    builder_1: ir.IRBuilder,
    value_1: ir.Value,
    builder_2: ir.IRBuilder,
    value_2: ir.Value,
) -> R[Value]:
    def inner() -> Value:
        phi = builder.phi(union_types(value_1.type, value_2.type))
        phi.add_incoming(value_1, builder_1.block)
        phi.add_incoming(value_2, builder_2.block)
        return box_value(phi)

    return (
        box_block_ref(builder).phi(
            Pair.create(box_value(value_1), box_block_ref(builder_1)),
            Pair.create(box_value(value_2), box_block_ref(builder_2)),
        ),
        inner,
    )


@register_llvmlite
@rule
def value_constant(tp: ir.Type, value: typing.Any) -> R[Value]:
    return (
        Value.constant(box_type(tp), value),
        lambda: box_value(ir.Constant(tp, value)),
    )


@register_llvmlite
@rule
def create_box_fn(
    fn: ir.Function,
    builder: ir.IRBuilder,
    terminate: Terminate,
    terminates: typing.Sequence[Terminate],
):
    fn_ref = box_fn_ref(fn)
    # Remove blocks that have already been added
    yield fn_ref.fn(box_terminate(builder), *terminates), fn_ref.fn(*terminates)

    # If we have added all, used fn_ref
    yield fn_ref.fn(), box_fn(fn)


@register_llvmlite
@rule
def create_box_mod(
    mod: ir.Module, ir_fn: ir.Function, fn: Fn, fns: typing.Sequence[Fn]
):
    mod_ref = box_mod_ref(mod)
    yield mod_ref.mod(box_fn(ir_fn), *fns), mod_ref.mod(*fns)
    yield mod_ref.mod(), box_mod(mod)


@register_llvmlite
@rule
def mod_str_rule(mod: ir.Module):
    return mod_str(box_mod(mod)), lambda: str(mod)

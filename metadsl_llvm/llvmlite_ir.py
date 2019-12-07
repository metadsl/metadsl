"""
Generate LLVM IR
"""

from __future__ import annotations

# TODO: make supertype things dunder so they don't interfere

# Support level of indirection to allow for mutable functions
# (support this as Mutates[...] like fortran, in, out, inout)

# Meta level transformations... Taking things like returning
# pairs of things and changing to mutate passed in args!

# Basically rewrites at the meta level? Or too many layers?

# Tradeoff  of making it harder to have client implementation with
# confusion

# CONCLUSION: Dont do at meta level, just support first class
# with Mutates[...] added to args which creates GDT of the arg names
# + the return type, if there is one.

# TODO: Allow doing *(CreateThing(x) for x in ...)
# To match a list of a certain expression

# TODO: Support returning multiple values?: NAW!


# TODO: Add dataclass like operator for storing  GDTs, so you don't have to define
# each getter method...
# To do this, need to be able to override __init__?

# How do I get access to original init? With super?
# Can't subclass expression... So instead wrap dataclass class in decorator.

# TODO: Why are docstrings wrong for Expressions?
# A: Ah.... I am trying to do init instead of create

# TODO: Can we have annotations be lazy in some way so we can define type below and then have it added?
import typing

import llvmlite.ir as ir

from metadsl import *
from metadsl_core import *

from .rules import register_llvmlite_ir_ref, register_llvmlite_ir

# TODO: Combine builders with references?
# Yes, try this, then then context can just be the values? But inverted
# Then, they will be pairs of values, still have current context but point to
# actual thing instead of builder

# So should block have vector of instructions instead of Block Builder as arg?
# Or should others have builder as arg instead of vector?

# 1. remove vec[xxx] from things and replace with builders (removes need for complicated transforms)
# 2. Remove references, and just have builders.
# 3. Have context use
__all__ = [
    "ModuleBuilder",
    "Type",
    "FunctionType",
    "FunctionBuilder",
    "BlockBuilder",
    "Value",
    "Function",
    "Module",
    "Value",
]


@hash_value.register
def hash_llvmlite_type(value: ir.Type) -> int:
    return hash((type(value), value._to_string()))


class ModuleBuilder(Expression):
    @expression
    @classmethod
    def create(cls, name: str) -> ModuleBuilder:
        ...

    @expression
    @classmethod
    def box(cls, module: ir.Module) -> ModuleBuilder:
        ...


class Type(Expression):
    @expression
    @classmethod
    def create_int(cls, bits: int) -> Type:
        ...

    @expression
    @classmethod
    def box(cls, type: ir.Type) -> Type:
        ...

    @expression
    def __or__(self, other: Type) -> Type:
        """
        Returns a type union of the two. By default this just verifies they
        are the same, otherwise it fails. 
        """
        ...


class FunctionType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: Type, *arg_types: Type) -> FunctionType:
        ...

    @expression
    @classmethod
    def box(cls, type: ir.FunctionType) -> FunctionType:
        ...


class FunctionBuilder(Expression):
    @expression
    @classmethod
    def create(
        cls,
        mod_builder: ModuleBuilder,
        type: FunctionType,
        name: str,
        calling_convention: str = "",
    ) -> Pair[ModuleBuilder, FunctionBuilder]:
        ...

    @expression
    @classmethod
    def box(cls, function: ir.Function) -> FunctionBuilder:
        ...

    @expression  # type: ignore
    @property
    def arguments(self) -> Vec[Value]:
        ...

    @expression  # type: ignore
    @property
    def type(self) -> FunctionType:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
        ...


class BlockBuilder(Expression):
    @expression
    @classmethod
    def create(
        cls, name: str, fn_builder: FunctionBuilder
    ) -> Pair[FunctionBuilder, BlockBuilder]:
        ...

    @expression
    @classmethod
    def box(cls, builder: ir.IRBuilder) -> BlockBuilder:
        ...

    @expression
    def icmp_signed(
        self, operator: str, left: Value, right: Value
    ) -> Pair[BlockBuilder, Value]:
        ...

    @expression
    def ret(self, value: Value) -> BlockBuilder:
        ...

    @expression
    def call(
        self, function: FunctionBuilder, args: Vec[Value]
    ) -> Pair[BlockBuilder, Value]:
        ...

    @expression
    def cbranch(
        self, condition: Value, true: BlockBuilder, false: BlockBuilder
    ) -> BlockBuilder:
        ...

    @expression
    def add(self, left: Value, right: Value) -> Pair[BlockBuilder, Value]:
        ...

    @expression
    def sub(self, left: Value, right: Value) -> Pair[BlockBuilder, Value]:
        ...

    @expression
    def alloca(self, type: Type) -> Pair[BlockBuilder, Value]:
        ...


class Value(Expression):
    @expression
    @classmethod
    def constant(cls, type: Type, value: typing.Any) -> Value:
        ...

    @expression
    @classmethod
    def box(cls, value: ir.Value) -> Value:
        ...

    @expression  # type: ignore
    @property
    def type(self) -> Type:
        ...


class Function(Expression):
    @expression
    @classmethod
    def create(cls, builder: FunctionBuilder, blocks: Vec[BlockBuilder]) -> Function:
        ...

    @expression  # type: ignore
    @property
    def builder(self) -> FunctionBuilder:
        ...

    @expression  # type: ignore
    @property
    def blocks(self) -> Vec[BlockBuilder]:
        ...

    @expression
    @classmethod
    def box(cls, function: ir.Function) -> Function:
        ...


class Module(Expression):
    @expression
    @classmethod
    def create(cls, module_builder: ModuleBuilder, functions: Vec[Function]) -> Module:
        ...

    @expression
    @classmethod
    def box(cls, module: ir.Module) -> Module:
        ...

    @expression  # type: ignore
    @property
    def functions(self) -> Vec[Function]:
        ...

    @expression  # type: ignore
    @property
    def builder(self) -> ModuleBuilder:
        ...
    @expression
    def to_string(self) -> str:
        ...


@register_llvmlite_ir_ref
@rule
def module_builder_box(name: str) -> R[ModuleBuilder]:
    return ModuleBuilder.create(name), lambda: ModuleBuilder.box(ir.Module(name))


@register_llvmlite_ir_ref
@rule
def type_create_int_box(bits: int) -> R[Type]:
    return Type.create_int(bits), lambda: Type.box(ir.IntType(bits))


@register_llvmlite_ir_ref
@rule
def type_or(l: ir.Type, r: ir.Type) -> R[Type]:
    def res() -> Type:
        if l != r:
            raise NoMatch()
        return Type.box(l)

    return Type.box(l) | Type.box(r), res


@register_llvmlite_ir_ref
@rule
def function_type_box_1(ret: ir.Type, arg1: ir.Type) -> R[FunctionType]:
    return (
        FunctionType.create(Type.box(ret), Type.box(arg1)),
        lambda: FunctionType.box(ir.FunctionType(ret, (arg1,))),
    )


@register_llvmlite_ir_ref
@rule
def function_type_box_2(ret: ir.Type, arg1: ir.Type, arg2: ir.Type) -> R[FunctionType]:
    return (
        FunctionType.create(Type.box(ret), Type.box(arg1), Type.box(arg2)),
        lambda: FunctionType.box(ir.FunctionType(ret, (arg1, arg2))),
    )


@register_llvmlite_ir_ref
@rule
def function_type_box_3(
    ret: ir.Type, arg1: ir.Type, arg2: ir.Type, arg3: ir.Type
) -> R[FunctionType]:
    return (
        FunctionType.create(
            Type.box(ret), Type.box(arg1), Type.box(arg2), Type.box(arg3)
        ),
        lambda: FunctionType.box(ir.FunctionType(ret, (arg1, arg2, arg3))),
    )


@register
@rule
def function_builder_type(
    module: ModuleBuilder, type: FunctionType, name: str, calling_convention: str
) -> R[FunctionType]:
    return (
        FunctionBuilder.create(module, type, name, calling_convention).right.type,
        type,
    )


@register
@rule
def function_builder_name(
    module: ModuleBuilder, type: FunctionType, name: str, calling_convention: str
) -> R[str]:
    return (
        FunctionBuilder.create(module, type, name, calling_convention).right.name,
        name,
    )


@register_llvmlite_ir_ref
@rule
def function_builder_create(
    mod: ir.Module, function_type: FunctionType, name: str, calling_convention: str
) -> R[ModuleBuilder]:
    return (
        FunctionBuilder.create(
            ModuleBuilder.box(mod), function_type, name, calling_convention
        ).left,
        ModuleBuilder.box(mod),
    )


@register_llvmlite_ir_ref
@rule
def function_builder_box(
    mod: ir.Module, fntype: ir.FunctionType, name: str, calling_convention: str
) -> R[FunctionBuilder]:
    def inner() -> FunctionBuilder:
        fn = ir.Function(mod, fntype, name)
        fn.calling_convention = calling_convention
        return FunctionBuilder.box(fn)

    return (
        FunctionBuilder.create(
            ModuleBuilder.box(mod), FunctionType.box(fntype), name, calling_convention
        ).right,
        inner,
    )


@register_llvmlite_ir_ref
@rule
def function_builder_arguments(function: ir.Function) -> R[Vec[Value]]:
    return (
        FunctionBuilder.box(function).arguments,
        lambda: Vec.create(*(Value.box(a) for a in function.args)),
    )


@register_llvmlite_ir_ref
@rule
def block_builder_box(
    function: ir.Function, name: str
) -> R[Pair[FunctionBuilder, BlockBuilder]]:
    return (
        BlockBuilder.create(name, FunctionBuilder.box(function)),
        lambda: Pair.create(
            FunctionBuilder.box(function),
            BlockBuilder.box(ir.IRBuilder(function.append_basic_block(name))),
        ),
    )


@register_llvmlite_ir_ref
@rule
def value_constant(tp: ir.Type, value: typing.Any) -> R[Value]:
    return (
        Value.constant(Type.box(tp), value),
        lambda: Value.box(ir.Constant(tp, value)),
    )


@register_llvmlite_ir_ref
@rule
def value_type(value: ir.Value) -> R[Type]:
    return (Value.box(value).type, lambda: Type.box(value.type))


@register_llvmlite_ir_ref
@rule
def builder_icmp_unsigned(
    builder: ir.IRBuilder, operator: str, left: ir.Value, right: ir.Value
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.icmp_signed(operator, Value.box(left), Value.box(right)),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.icmp_unsigned(operator, left, right))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_ret(builder: ir.IRBuilder, value: ir.Value) -> R[BlockBuilder]:
    builder_ = BlockBuilder.box(builder)

    def inner():
        builder.ret(value)
        return builder_

    return (builder_.ret(Value.box(value)), inner)


@register_llvmlite_ir_ref
@rule
def builder_call_1(
    builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.call(FunctionBuilder.box(function), Vec.create(Value.box(arg1))),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.call(function, (arg1,)))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_call_2(
    builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value, arg2: ir.Value
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.call(
            FunctionBuilder.box(function), Vec.create(Value.box(arg1), Value.box(arg2)),
        ),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.call(function, (arg1, arg2)))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_call_3(
    builder: ir.IRBuilder,
    function: ir.Function,
    arg1: ir.Value,
    arg2: ir.Value,
    arg3: ir.Value,
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.call(
            FunctionBuilder.box(function),
            Vec.create(Value.box(arg1), Value.box(arg2), Value.box(arg3)),
        ),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.call(function, (arg1, arg2, arg3)))
        ),
    )


# # TODO: Support creating iterations of values in matches to make this variadic:
# """
# @register_llvmlite_ir_ref
# @rule
# def builder_call(
#     builder: ir.IRBuilder, function: ir.Function, values: typing.Sequence[ir.Value]
# ) -> R[Pair[BlockBuilder, Value]]:
#     builder_ = BlockBuilder.box(builder)
#     return (
#         builder_.call(
#             FunctionBuilder.box(function),
#             Vec.create(*(Value.box(value) for value in values)),
#         ),
#         lambda: Pair[BlockBuilder, Value].create(
#             builder_, Value.box(builder.call(function, tuple(values)))
#         ),
#     )
# """


@register_llvmlite_ir_ref
@rule
def builder_cbranch(
    builder: ir.IRBuilder, cond: ir.Value, true: ir.IRBuilder, false: ir.IRBuilder
) -> R[BlockBuilder]:
    builder_ = BlockBuilder.box(builder)

    def inner() -> BlockBuilder:
        builder.cbranch(cond, true.block, false.block)
        return builder_

    return (
        builder_.cbranch(
            Value.box(cond), BlockBuilder.box(true), BlockBuilder.box(false)
        ),
        inner,
    )


@register_llvmlite_ir_ref
@rule
def builder_add(
    builder: ir.IRBuilder, left: ir.Value, right: ir.Value
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.add(Value.box(left), Value.box(right)),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.add(left, right))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_sub(
    builder: ir.IRBuilder, left: ir.Value, right: ir.Value
) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.sub(Value.box(left), Value.box(right)),
        lambda: Pair[BlockBuilder, Value].create(
            builder_, Value.box(builder.sub(left, right))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_alloca(builder: ir.IRBuilder, tp: ir.Type) -> R[Pair[BlockBuilder, Value]]:
    builder_ = BlockBuilder.box(builder)
    return (
        builder_.alloca(Type.box(tp)),
        lambda: Pair.create(builder_, Value.box(builder.alloca(tp))),
    )


@register_llvmlite_ir
@rule
def function_box_1(fn: ir.Function, block1: ir.IRBuilder) -> R[Function]:
    return (
        Function.create(FunctionBuilder.box(fn), Vec.create(BlockBuilder.box(block1))),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_2(
    fn: ir.Function, block1: ir.IRBuilder, block2: ir.IRBuilder
) -> R[Function]:
    return (
        Function.create(
            FunctionBuilder.box(fn),
            Vec.create(BlockBuilder.box(block1), BlockBuilder.box(block2)),
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_3(
    fn: ir.Function, block1: ir.IRBuilder, block2: ir.IRBuilder, block3: ir.IRBuilder
) -> R[Function]:
    return (
        Function.create(
            FunctionBuilder.box(fn),
            Vec.create(
                BlockBuilder.box(block1),
                BlockBuilder.box(block2),
                BlockBuilder.box(block3),
            ),
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_4(
    fn: ir.Function,
    block1: ir.IRBuilder,
    block2: ir.IRBuilder,
    block3: ir.IRBuilder,
    block4: ir.IRBuilder,
) -> R[Function]:
    return (
        Function.create(
            FunctionBuilder.box(fn),
            Vec.create(
                BlockBuilder.box(block1),
                BlockBuilder.box(block2),
                BlockBuilder.box(block3),
                BlockBuilder.box(block4),
            ),
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_5(
    fn: ir.Function,
    block1: ir.IRBuilder,
    block2: ir.IRBuilder,
    block3: ir.IRBuilder,
    block4: ir.IRBuilder,
    block5: ir.IRBuilder,
) -> R[Function]:
    return (
        Function.create(
            FunctionBuilder.box(fn),
            Vec.create(
                BlockBuilder.box(block1),
                BlockBuilder.box(block2),
                BlockBuilder.box(block3),
                BlockBuilder.box(block4),
                BlockBuilder.box(block5),
            ),
        ),
        lambda: Function.box(fn),
    )


@register
@rule
def function_builder(
    fn: FunctionBuilder, blocks: Vec[BlockBuilder]
) -> R[FunctionBuilder]:
    return Function.create(fn, blocks).builder, fn


@register
@rule
def function_blocks(
    fn: FunctionBuilder, blocks: Vec[BlockBuilder]
) -> R[Vec[BlockBuilder]]:
    return Function.create(fn, blocks).blocks, blocks


@register_llvmlite_ir
@rule
def module_box_1(mod: ir.Module, fn1: ir.Function) -> R[Module]:
    return (
        Module.create(ModuleBuilder.box(mod), Vec.create(Function.box(fn1))),
        Module.box(mod),
    )


@register_llvmlite_ir
@rule
def module_box_2(mod: ir.Module, fn1: ir.Function, fn2: ir.Function) -> R[Module]:
    return (
        Module.create(
            ModuleBuilder.box(mod), Vec.create(Function.box(fn1), Function.box(fn2))
        ),
        Module.box(mod),
    )


@register_llvmlite_ir
@rule
def module_box_3(
    mod: ir.Module, fn1: ir.Function, fn2: ir.Function, fn3: ir.Function
) -> R[Module]:
    return (
        Module.create(
            ModuleBuilder.box(mod),
            Vec.create(Function.box(fn1), Function.box(fn2), Function.box(fn3)),
        ),
        Module.box(mod),
    )


@register_llvmlite_ir
@rule
def module_to_string(mod: ir.Module) -> R[str]:
    return Module.box(mod).to_string(), lambda: str(mod)


@register
@rule
def module_builder(
    builder: ModuleBuilder, functions: Vec[Function]
) -> R[ModuleBuilder]:
    return Module.create(builder, functions).builder, builder


@register
@rule
def module_functions(
    reference: ModuleBuilder, functions: Vec[Function]
) -> R[Vec[Function]]:
    return Module.create(reference, functions).functions, functions


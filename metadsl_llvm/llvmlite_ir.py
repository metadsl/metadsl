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


__all__ = [
    "Module",
    "ModuleReference",
    "Type",
    "FunctionType",
    "Function",
    "FunctionReference",
    "Block",
    "BlockReference",
    "Builder",
    "BuilderValue",
    "Value",
]


@hash_value.register
def hash_llvmlite_type(value: ir.Type) -> int:
    return hash((type(value), value._to_string()))


class Module(Expression):
    @expression
    @classmethod
    def create(cls, reference: ModuleReference, functions: Vec[Function]) -> Module:
        ...

    @property  # type: ignore
    @expression
    def reference(self) -> ModuleReference:
        ...

    @property  # type: ignore
    @expression
    def functions(self) -> Vec[Function]:
        ...

    @expression
    def to_string(self) -> str:
        ...

    @expression
    @classmethod
    def box(cls, module: ir.Module) -> Module:
        ...


@register_llvmlite_ir
@rule
def module_to_string(mod: ir.Module) -> R[str]:
    return Module.box(mod).to_string(), lambda: str(mod)


class ModuleReference(Expression):
    @expression
    @classmethod
    def create(cls, name: str) -> ModuleReference:
        ...

    @expression
    @classmethod
    def box(cls, module: ir.Module) -> ModuleReference:
        ...


@register_llvmlite_ir_ref
@rule
def module_reference_box(name: str) -> R[ModuleReference]:
    return ModuleReference.create(name), lambda: ModuleReference.box(ir.Module(name))


class Type(Expression):
    @expression
    @classmethod
    def create_int(cls, bits: int) -> Type:
        ...

    @expression
    @classmethod
    def box(cls, type: ir.Type) -> Type:
        ...


@register_llvmlite_ir_ref
@rule
def type_create_int_box(bits: int) -> R[Type]:
    return Type.create_int(bits), lambda: Type.box(ir.IntType(bits))


class FunctionType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: Type, *arg_types: Type) -> FunctionType:
        ...

    @expression
    @classmethod
    def box(cls, type: ir.FunctionType) -> FunctionType:
        ...


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


class Function(Expression):
    @expression
    @classmethod
    def create(self, reference: FunctionReference, blocks: Vec[Block]) -> Function:
        ...

    @property  # type: ignore
    @expression
    def reference(self) -> FunctionReference:
        ...

    @expression
    @classmethod
    def box(cls, function: ir.Function) -> Function:
        ...


@register_llvmlite_ir
@rule
def module_box(mod: ir.Module, functions: Vec[Function]) -> R[Module]:
    return Module.create(ModuleReference.box(mod), functions), Module.box(mod)


@register
@rule
def module_reference(
    reference: ModuleReference, functions: Vec[Function]
) -> R[ModuleReference]:
    return Module.create(reference, functions).reference, reference


@register
@rule
def module_functions(
    reference: ModuleReference, functions: Vec[Function]
) -> R[Vec[Function]]:
    return Module.create(reference, functions).functions, functions


class FunctionReference(Expression):
    @expression
    @classmethod
    def create(
        self,
        module: ModuleReference,
        type: FunctionType,
        name: str,
        calling_convention: str = "",
    ) -> FunctionReference:
        ...

    @property  # type: ignore
    @expression
    def arguments(self) -> Vec[Value]:
        ...

    @property  # type: ignore
    @expression
    def type(self) -> FunctionType:
        ...

    @property  # type: ignore
    @expression
    def name(self) -> str:
        ...

    @property  # type: ignore
    @expression
    def module(self) -> ModuleReference:
        ...

    @expression
    @classmethod
    def box(cls, function: ir.Function) -> FunctionReference:
        ...


@register
@rule
def function_reference_type(
    module: ModuleReference, type: FunctionType, name: str, calling_convention: str
) -> R[FunctionType]:
    return (FunctionReference.create(module, type, name, calling_convention).type, type)


@register
@rule
def function_reference_name(
    module: ModuleReference, type: FunctionType, name: str, calling_convention: str
) -> R[str]:
    return (FunctionReference.create(module, type, name, calling_convention).name, name)


@register
@rule
def function_reference_module(
    module: ModuleReference, type: FunctionType, name: str, calling_convention: str
) -> R[ModuleReference]:
    return (
        FunctionReference.create(module, type, name, calling_convention).module,
        module,
    )


@register_llvmlite_ir_ref
@rule
def function_reference_box(
    mod: ir.Module, fntype: ir.FunctionType, name: str, calling_convention: str
) -> R[FunctionReference]:
    def inner() -> FunctionReference:
        fn = ir.Function(mod, fntype, name)
        fn.calling_convention = calling_convention
        return FunctionReference.box(fn)

    return (
        FunctionReference.create(
            ModuleReference.box(mod), FunctionType.box(fntype), name, calling_convention
        ),
        inner,
    )


class Block(Expression):
    @expression
    @classmethod
    def create(cls, reference: BlockReference, builder: Builder) -> Block:
        ...

    @expression
    @classmethod
    def box(cls, block: ir.Block) -> Block:
        ...


# TODO: replace with looping varient when we support that in matching
@register_llvmlite_ir
@rule
def function_box_1(fn: ir.Function, block1: ir.Block) -> R[Function]:
    return (
        Function.create(FunctionReference.box(fn), Vec.create(Block.box(block1))),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_2(fn: ir.Function, block1: ir.Block, block2: ir.Block) -> R[Function]:
    return (
        Function.create(
            FunctionReference.box(fn), Vec.create(Block.box(block1), Block.box(block2))
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_3(
    fn: ir.Function, block1: ir.Block, block2: ir.Block, block3: ir.Block
) -> R[Function]:
    return (
        Function.create(
            FunctionReference.box(fn),
            Vec.create(Block.box(block1), Block.box(block2), Block.box(block3)),
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_4(
    fn: ir.Function,
    block1: ir.Block,
    block2: ir.Block,
    block3: ir.Block,
    block4: ir.Block,
) -> R[Function]:
    return (
        Function.create(
            FunctionReference.box(fn),
            Vec.create(
                Block.box(block1),
                Block.box(block2),
                Block.box(block3),
                Block.box(block4),
            ),
        ),
        lambda: Function.box(fn),
    )


@register_llvmlite_ir
@rule
def function_box_5(
    fn: ir.Function,
    block1: ir.Block,
    block2: ir.Block,
    block3: ir.Block,
    block4: ir.Block,
    block5: ir.Block,
) -> R[Function]:
    return (
        Function.create(
            FunctionReference.box(fn),
            Vec.create(
                Block.box(block1),
                Block.box(block2),
                Block.box(block3),
                Block.box(block4),
                Block.box(block5),
            ),
        ),
        lambda: Function.box(fn),
    )


class BlockReference(Expression):
    @expression
    @classmethod
    def create(cls, name: str, function: FunctionReference) -> BlockReference:
        ...

    @expression
    @classmethod
    def box(cls, block: ir.Block) -> BlockReference:
        ...


@register_llvmlite_ir_ref
@rule
def block_reference_box(function: ir.Function, name: str) -> R[BlockReference]:
    return (
        BlockReference.create(name, FunctionReference.box(function)),
        lambda: BlockReference.box(function.append_basic_block(name)),
    )


class Builder(Expression):
    @expression
    @classmethod
    def create(cls, block: BlockReference) -> Builder:
        ...

    @expression
    @classmethod
    def box(cls, builder: ir.IRBuilder) -> Builder:
        ...

    @expression
    def icmp_signed(self, operator: str, left: Value, right: Value) -> BuilderValue:
        ...

    @expression
    def ret(self, value: Value) -> Builder:
        ...

    @expression
    def call(self, function: FunctionReference, args: Vec[Value]) -> BuilderValue:
        ...

    @expression
    def cbranch(
        self, condition: Value, true: BlockReference, false: BlockReference
    ) -> Builder:
        ...

    @expression
    def add(self, left: Value, right: Value) -> BuilderValue:
        ...

    @expression
    def sub(self, left: Value, right: Value) -> BuilderValue:
        ...


@register_llvmlite_ir
@rule
def block_box(block: ir.Block, builder: ir.IRBuilder) -> R[Block]:
    return (
        Block.create(BlockReference.box(block), Builder.box(builder)),
        lambda: Block.box(block),
    )


@register_llvmlite_ir_ref
@rule
def builder_box(block: ir.Block) -> R[Builder]:
    return (
        Builder.create(BlockReference.box(block)),
        lambda: Builder.box(ir.IRBuilder(block)),
    )


class Value(Expression):
    @expression
    @classmethod
    def constant(cls, type: Type, value: typing.Any) -> Value:
        ...

    @expression
    @classmethod
    def box(cls, value: ir.Value) -> Value:
        ...


@register_llvmlite_ir_ref
@rule
def value_constant(tp: ir.Type, value: typing.Any) -> R[Value]:
    return (
        Value.constant(Type.box(tp), value),
        lambda: Value.box(ir.Constant(tp, value)),
    )


@register_llvmlite_ir_ref
@rule
def function_reference_arguments(function: ir.Function) -> R[Vec[Value]]:
    return (
        FunctionReference.box(function).arguments,
        lambda: Vec.create(*(Value.box(a) for a in function.args)),
    )


class BuilderValue(Expression):
    """
    Same as Pair[Builder, Value] but has different method names, for better debugging.
    """

    @expression
    @classmethod
    def create(cls, builder: Builder, value: Value) -> BuilderValue:
        ...

    @property  # type: ignore
    @expression
    def builder(self) -> Builder:
        ...

    @property  # type: ignore
    @expression
    def value(self) -> Value:
        ...


@register
@rule
def builder_value_builder(builder: Builder, value: Value) -> R[Builder]:
    return BuilderValue.create(builder, value).builder, builder


@register
@rule
def builder_value_value(builder: Builder, value: Value) -> R[Value]:
    return BuilderValue.create(builder, value).value, value


@register_llvmlite_ir_ref
@rule
def builder_icmp_unsigned(
    builder: ir.IRBuilder, operator: str, left: ir.Value, right: ir.Value
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.icmp_signed(operator, Value.box(left), Value.box(right)),
        lambda: BuilderValue.create(
            builder_, Value.box(builder.icmp_unsigned(operator, left, right))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_ret(builder: ir.IRBuilder, value: ir.Value) -> R[Builder]:
    builder_ = Builder.box(builder)

    def inner():
        builder.ret(value)
        return builder_

    return (builder_.ret(Value.box(value)), inner)


@register_llvmlite_ir_ref
@rule
def builder_call_1(
    builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.call(FunctionReference.box(function), Vec.create(Value.box(arg1))),
        lambda: BuilderValue.create(
            builder_, Value.box(builder.call(function, (arg1,)))
        ),
    )


@register_llvmlite_ir_ref
@rule
def builder_call_2(
    builder: ir.IRBuilder, function: ir.Function, arg1: ir.Value, arg2: ir.Value
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.call(
            FunctionReference.box(function),
            Vec.create(Value.box(arg1), Value.box(arg2)),
        ),
        lambda: BuilderValue.create(
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
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.call(
            FunctionReference.box(function),
            Vec.create(Value.box(arg1), Value.box(arg2), Value.box(arg3)),
        ),
        lambda: BuilderValue.create(
            builder_, Value.box(builder.call(function, (arg1, arg2, arg3)))
        ),
    )


# TODO: Support creating iterations of values in matches to make this variadic:
"""
@register_llvmlite_ir_ref
@rule
def builder_call(
    builder: ir.IRBuilder, function: ir.Function, values: typing.Sequence[ir.Value]
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.call(
            FunctionReference.box(function),
            Vec.create(*(Value.box(value) for value in values)),
        ),
        lambda: BuilderValue.create(
            builder_, Value.box(builder.call(function, tuple(values)))
        ),
    )
"""


@register_llvmlite_ir_ref
@rule
def builder_cbranch(
    builder: ir.IRBuilder, cond: ir.Value, true: ir.Block, false: ir.Block
) -> R[Builder]:
    builder_ = Builder.box(builder)

    def inner() -> Builder:
        builder.cbranch(cond, true, false)
        return builder_

    return (
        builder_.cbranch(
            Value.box(cond), BlockReference.box(true), BlockReference.box(false)
        ),
        inner,
    )


@register_llvmlite_ir_ref
@rule
def builder_add(
    builder: ir.IRBuilder, left: ir.Value, right: ir.Value
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.add(Value.box(left), Value.box(right)),
        lambda: BuilderValue.create(builder_, Value.box(builder.add(left, right))),
    )


@register_llvmlite_ir_ref
@rule
def builder_sub(
    builder: ir.IRBuilder, left: ir.Value, right: ir.Value
) -> R[BuilderValue]:
    builder_ = Builder.box(builder)
    return (
        builder_.sub(Value.box(left), Value.box(right)),
        lambda: BuilderValue.create(builder_, Value.box(builder.sub(left, right))),
    )

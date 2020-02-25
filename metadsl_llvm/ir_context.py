"""
Dataflow based LLVMLite IR to create LLVMLite IR.
"""

from __future__ import annotations

import typing
import functools

from metadsl import *
from metadsl_core import *

from .ir import *
from .integration import *

__all__ = ["ir_context_rules", "llvm_fn", "to_llvm", "ValueExpr"]

ir_context_rules = RulesRepeatFold()
register_context = ir_context_rules.append


BlockCtx = Pair[BlockRef, Fn]
ValueCtx = Pair[Value, BlockCtx]


class ValueExpr(Expression):
    @expression
    def build(self, block_ctx: BlockCtx) -> ValueCtx:
        """
        Given some block, add the values to this block by adding instructions to it, or making
        new blocks on this function.
        """

        ...

    @expression
    def __add__(self, right: ValueExpr) -> ValueExpr:
        ...

    @expression
    def __sub__(self, right: ValueExpr) -> ValueExpr:
        ...

    @expression
    def if_(self, true: ValueExpr, false: ValueExpr) -> ValueExpr:
        ...

    @expression
    @classmethod
    def from_value(cls, val: Value) -> ValueExpr:
        ...

    def __lt__(self, other: ValueExpr) -> ValueExpr:
        return self.icmp_signed("<", other)

    def __gt__(self, other: ValueExpr) -> ValueExpr:
        return self.icmp_signed(">", other)

    def eq(self, other: ValueExpr) -> ValueExpr:
        return self.icmp_signed("==", other)

    @expression
    def icmp_signed(self, operator: str, right: ValueExpr) -> ValueExpr:
        ...


AllFns = typing.Union[
    FunctionOne[ValueExpr, ValueExpr],
    FunctionTwo[ValueExpr, ValueExpr, ValueExpr],
    FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
]

SomeFn = typing.TypeVar("SomeFn", bound=AllFns)


@expression
def from_llvm_fn_1(fn: Fn) -> FunctionOne[ValueExpr, ValueExpr]:
    ...


@expression
def from_llvm_fn_2(fn: Fn) -> FunctionTwo[ValueExpr, ValueExpr, ValueExpr]:
    ...


@expression
def from_llvm_fn_3(fn: Fn) -> FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr]:
    ...


def llvm_fn(mod_ref: ModRef, fn_tp: FnType) -> typing.Callable[[SomeFn], SomeFn]:
    def inner(fn: SomeFn, mod_ref=mod_ref, fn_tp=fn_tp) -> SomeFn:
        if isinstance(fn, FunctionOne):
            return llvm_fn_1(fn, mod_ref, fn_tp)  # type: ignore
        elif isinstance(fn, FunctionTwo):  # type: ignore
            return llvm_fn_2(fn, mod_ref, fn_tp)  # type: ignore
        return llvm_fn_3(fn, mod_ref, fn_tp)  # type: ignore

    return inner


@expression
def llvm_fn_1(
    fn: FunctionOne[ValueExpr, ValueExpr], mod_ref: ModRef, fn_tp: FnType
) -> FunctionOne[ValueExpr, ValueExpr]:
    ...


@expression
def llvm_fn_2(
    fn: FunctionTwo[ValueExpr, ValueExpr, ValueExpr], mod_ref: ModRef, fn_tp: FnType
) -> FunctionTwo[ValueExpr, ValueExpr, ValueExpr]:
    ...


@expression
def llvm_fn_3(
    fn: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
    mod_ref: ModRef,
    fn_tp: FnType,
) -> FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr]:
    ...


def to_llvm(fn: AllFns) -> Fn:
    if isinstance(fn, FunctionOne):
        return to_llvm_fn_1(fn)
    elif isinstance(fn, FunctionTwo):
        return to_llvm_fn_2(fn)
    return to_llvm_fn_3(fn)


@typing.overload
def _fn_n_rule(
    mod_ref: ModRef, fn_n: FunctionOne[ValueExpr, ValueExpr], fn_tp: FnType,
) -> R[FunctionOne[ValueExpr, ValueExpr]]:
    ...


@typing.overload
def _fn_n_rule(
    mod_ref: ModRef, fn_n: FunctionTwo[ValueExpr, ValueExpr, ValueExpr], fn_tp: FnType,
) -> R[FunctionTwo[ValueExpr, ValueExpr, ValueExpr]]:
    ...


@typing.overload
def _fn_n_rule(
    mod_ref: ModRef,
    fn_n: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
    fn_tp: FnType,
) -> R[FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr]]:
    ...


def _fn_n_rule(mod_ref: ModRef, fn_n: AllFns, fn_tp: FnType,) -> R[AllFns]:
    fn_ref = mod_ref.fn(fn_n.name, fn_tp, "fastcc")

    # Use this to pass into fixed point operator so it can call itself
    tmp_fn = fn_ref.fn()
    fn_expr: AllFns
    if isinstance(fn_n, FunctionOne):
        fn_expr = llvm_fn_1(fn_n, mod_ref, fn_tp)
        fn_res = fn_n.unfix(from_llvm_fn_1(tmp_fn))(
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)])
        )
    elif isinstance(fn_n, FunctionTwo):
        fn_expr = llvm_fn_2(fn_n, mod_ref, fn_tp)
        fn_res = fn_n.unfix(from_llvm_fn_2(tmp_fn))(
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(1)]),
        )
    else:
        fn_expr = llvm_fn_3(fn_n, mod_ref, fn_tp)
        fn_res = fn_n.unfix(from_llvm_fn_3(tmp_fn))(
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(1)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(2)]),
        )
    res_val, res_block_ctx = fn_res.build(
        Pair.create(fn_ref.block(True), fn_ref.fn())
    ).spread
    block_ref, fn = res_block_ctx.spread
    fn = fn.add_block(block_ref.ret(res_val))
    if isinstance(fn_n, FunctionOne):
        fn_n = from_llvm_fn_1(fn)
    elif isinstance(fn_n, FunctionTwo):
        fn_n = from_llvm_fn_2(fn)
    else:
        fn_n = from_llvm_fn_3(fn)
    return (
        fn_expr,
        fn_n,
    )


@register_context
@rule
def llvm_fn_to_from_llvm_fn_1(
    fn_n: FunctionOne[ValueExpr, ValueExpr], mod_ref: ModRef, fn_tp: FnType
) -> R[FunctionOne[ValueExpr, ValueExpr]]:
    return _fn_n_rule(mod_ref, fn_n, fn_tp)


@register_context
@rule
def llvm_fn_to_from_llvm_fn_2(
    fn_n: FunctionTwo[ValueExpr, ValueExpr, ValueExpr], mod_ref: ModRef, fn_tp: FnType
) -> R[FunctionTwo[ValueExpr, ValueExpr, ValueExpr]]:
    return _fn_n_rule(mod_ref, fn_n, fn_tp)


@register_context
@rule
def llvm_fn_to_from_llvm_fn_3(
    fn_n: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
    mod_ref: ModRef,
    fn_tp: FnType,
) -> R[FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr]]:
    return _fn_n_rule(mod_ref, fn_n, fn_tp)


@expression
def to_llvm_fn_1(fn: FunctionOne[ValueExpr, ValueExpr]) -> Fn:
    ...


@expression
def to_llvm_fn_2(fn: FunctionTwo[ValueExpr, ValueExpr, ValueExpr]) -> Fn:
    ...


@expression
def to_llvm_fn_3(fn: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr]) -> Fn:
    ...


@register_context
@rule
def to_from_llvm_fn_1(fn: Fn) -> R[Fn]:
    yield to_llvm_fn_1(from_llvm_fn_1(fn)), fn
    yield to_llvm_fn_2(from_llvm_fn_2(fn)), fn
    yield to_llvm_fn_3(from_llvm_fn_3(fn)), fn


@register_context
@rule
def build_call_1(fn: Fn, arg: ValueExpr, block_ctx: BlockCtx) -> R[ValueCtx]:
    target = from_llvm_fn_1(fn)(arg).build(block_ctx)
    arg_v, block_ctx = arg.build(block_ctx).spread
    res = block_ctx.left.call(fn.ref, Vec.create(arg_v))
    return (target, Pair.create(res, block_ctx))


@register_context
@rule
def build_call_2(
    fn: Fn, arg1: ValueExpr, arg2: ValueExpr, block_ctx: BlockCtx
) -> R[ValueCtx]:
    target = from_llvm_fn_2(fn)(arg1, arg2).build(block_ctx)
    arg1_v, block_ctx = arg1.build(block_ctx).spread
    arg2_v, block_ctx = arg2.build(block_ctx).spread
    res = block_ctx.left.call(fn.ref, Vec.create(arg1_v, arg2_v))
    return (target, Pair.create(res, block_ctx))


@register_context
@rule
def build_call_3(
    fn: Fn, arg1: ValueExpr, arg2: ValueExpr, arg3: ValueExpr, block_ctx: BlockCtx
) -> R[ValueCtx]:
    target = from_llvm_fn_3(fn)(arg1, arg2, arg3).build(block_ctx)
    arg1_v, block_ctx = arg1.build(block_ctx).spread
    arg2_v, block_ctx = arg2.build(block_ctx).spread
    arg3_v, block_ctx = arg3.build(block_ctx).spread
    res = block_ctx.left.call(fn.ref, Vec.create(arg1_v, arg2_v, arg3_v))
    return (target, Pair.create(res, block_ctx))


@register_context
@rule
def build_add(l_exp: ValueExpr, r_exp: ValueExpr, block_ctx: BlockCtx) -> R[ValueCtx]:
    target = (l_exp + r_exp).build(block_ctx)

    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.add(l, r)
    return (target, Pair.create(res, block_ctx))


@register_context
@rule
def build_sub(l_exp: ValueExpr, r_exp: ValueExpr, block_ctx: BlockCtx) -> R[ValueCtx]:
    target = (l_exp - r_exp).build(block_ctx)

    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.sub(l, r)
    return (target, Pair.create(res, block_ctx))


@register_context
@rule
def build_icmp_signed(
    l_exp: ValueExpr, r_exp: ValueExpr, operator: str, block_ctx: BlockCtx,
) -> R[ValueCtx]:
    target = l_exp.icmp_signed(operator, r_exp).build(block_ctx)
    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.icmp_signed(operator, l, r)
    return (target, Pair.create(res, block_ctx))


def switch_block(
    block_ctx: BlockCtx, finished_block: Terminate, new_block: BlockRef
) -> BlockCtx:
    return Pair.create(new_block, block_ctx.right.add_block(finished_block))


@register_context
@rule
def build_cbranch(
    cond_exp: ValueExpr, true_exp: ValueExpr, false_exp: ValueExpr, block_ctx: BlockCtx,
) -> R[ValueCtx]:
    """
    Builds a cbranch from two expressions, by creating a block for the true and false
    expressions. In each block, the true and false are evaluated and then .
    Then, there is a after block that will load the right operation using phi.

    Based on https://llvm.org/docs/tutorial/OCamlLangImpl5.html#if-then-else
    """
    target = cond_exp.if_(true_exp, false_exp).build(block_ctx)

    # First build conditional expression on curent block, to get conditional value
    cond_res, block_ctx = cond_exp.build(block_ctx).spread

    # Then add new blocks
    fn_ref = block_ctx.right.ref
    true_block_ref = fn_ref.block(False, "cbranch_true")
    false_block_ref = fn_ref.block(False, "cbranch_false")
    after_block_ref = fn_ref.block(False, "cbranch_after")

    # Then cbranch to true/false blocks based on result
    initial_terminate = block_ctx.left.cbranch(
        cond_res, true_block_ref, false_block_ref
    )

    # Now switch to the true block to create that one
    block_ctx = switch_block(block_ctx, initial_terminate, true_block_ref)
    true_res, block_ctx = true_exp.build(block_ctx).spread
    true_terminate = block_ctx.left.branch(after_block_ref)

    # Finish this block and go to false block
    block_ctx = switch_block(block_ctx, true_terminate, false_block_ref)
    false_res, block_ctx = false_exp.build(block_ctx).spread
    false_terminate = block_ctx.left.branch(after_block_ref)

    # Now switch to the last after block
    block_ctx = switch_block(block_ctx, false_terminate, after_block_ref)
    final_value = block_ctx.left.phi(
        Pair.create(false_res, false_block_ref), Pair.create(true_res, true_block_ref)
    )

    return (target, Pair.create(final_value, block_ctx))


@register_context
@rule
def build_constant(value: Value, block_ctx: BlockCtx) -> R[ValueCtx]:
    return (ValueExpr.from_value(value).build(block_ctx), Pair.create(value, block_ctx))


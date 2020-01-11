"""
Dataflow based LLVMLite IR to create LLVMLite IR.
"""

from __future__ import annotations

import typing

from metadsl import *
from metadsl_core import *

from .ir import *
from .integration import *

__all__ = ["ir_context_rules", "ModExpr", "FnExpr", "ValueExpr"]

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


class ModExpr(Expression):
    @expression
    @classmethod
    def from_mod_ref(cls, ref: ModRef) -> ModExpr:
        ...

    def fn_dec(self, fn_tp: FnType) -> typing.Callable[[AllFns], FnExpr]:
        def inner(fn_n: AllFns, fn_tp=fn_tp) -> FnExpr:
            if isinstance(fn_n, FunctionOne):
                return self.fn_1(fn_n, fn_tp)
            elif isinstance(fn_n, FunctionTwo):
                return self.fn_2(fn_n, fn_tp)
            return self.fn_3(fn_n, fn_tp)

        return inner

    @expression
    def fn_1(self, fn: FunctionOne[ValueExpr, ValueExpr], fn_tp: FnType) -> FnExpr:
        ...

    @expression
    def fn_2(
        self, fn: FunctionTwo[ValueExpr, ValueExpr, ValueExpr], fn_tp: FnType
    ) -> FnExpr:
        ...

    @expression
    def fn_3(
        self,
        fn: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
        fn_tp: FnType,
    ) -> FnExpr:
        ...


class FnExpr(Expression):
    @expression
    def __call__(self, *args: ValueExpr) -> ValueExpr:
        ...

    @expression
    def compile(
        self, mod_ref: ModRef, *other_fns: FnExpr, optimization: int = 1
    ) -> typing.Callable:
        ...


@expression
def fn_expr_from_fn(fn: Fn) -> FnExpr:
    ...


@expression
def fn_expr_get_fn(fn: FnExpr) -> Fn:
    ...


@register_context
@rule
def fn_expr_id_rule(fn: Fn) -> R[Fn]:
    return (
        fn_expr_get_fn(fn_expr_from_fn(fn)),
        fn,
    )


def _fn_n_rule(ref: ModRef, fn_n: AllFns, fn_tp: FnType,) -> R[FnExpr]:
    mod_expr = ModExpr.from_mod_ref(ref)

    fn_ref = ref.fn(fn_n.name, fn_tp, "fastcc")
    if isinstance(fn_n, FunctionOne):
        fn_expr = mod_expr.fn_1(fn_n, fn_tp)
        fn_res = fn_n(ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)]))
    elif isinstance(fn_n, FunctionTwo):
        fn_expr = mod_expr.fn_2(fn_n, fn_tp)
        fn_res = fn_n(
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(1)]),
        )
    else:
        fn_expr = mod_expr.fn_3(fn_n, fn_tp)
        fn_res = fn_n(
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(0)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(1)]),
            ValueExpr.from_value(fn_ref.arguments[Integer.from_int(2)]),
        )
    res_val, res_block_ctx = fn_res.build(
        Pair.create(fn_ref.block(True), fn_ref.fn())
    ).spread
    block_ref, fn = res_block_ctx.spread

    return (
        fn_expr,
        fn_expr_from_fn(fn.add_block(block_ref.ret(res_val))),
    )


@register_context
@rule
def fn_1_rule(
    ref: ModRef, fn_1: FunctionOne[ValueExpr, ValueExpr], fn_tp: FnType
) -> R[FnExpr]:
    return _fn_n_rule(ref, fn_1, fn_tp)


@register_context
@rule
def fn_2_rule(
    ref: ModRef, fn_2: FunctionTwo[ValueExpr, ValueExpr, ValueExpr], fn_tp: FnType
) -> R[FnExpr]:
    return _fn_n_rule(ref, fn_2, fn_tp)


@register_context
@rule
def fn_3_rule(
    ref: ModRef,
    fn_3: FunctionThree[ValueExpr, ValueExpr, ValueExpr, ValueExpr],
    fn_tp: FnType,
) -> R[FnExpr]:
    return _fn_n_rule(ref, fn_3, fn_tp)


@register_context
@rule
def fn_compile_rule(
    mod_ref: ModRef, fn_expr: FnExpr, other_fn_exprs: typing.Sequence[FnExpr], o: int
) -> R[typing.Callable]:
    fn = fn_expr_get_fn(fn_expr)

    return (
        fn_expr.compile(mod_ref, *other_fn_exprs, optimization=o),
        compile_function(
            mod_ref.mod(fn, *(map(fn_expr_get_fn, other_fn_exprs))), fn.ref, o
        ),
    )


@register_context
@rule
def build_add(l_exp: ValueExpr, r_exp: ValueExpr, block_ctx: BlockCtx) -> R[ValueCtx]:
    target = (l_exp + r_exp).build(block_ctx)

    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.add(l, r)
    return (
        target,
        Pair.create(res, block_ctx),
    )


@register_context
@rule
def build_sub(l_exp: ValueExpr, r_exp: ValueExpr, block_ctx: BlockCtx) -> R[ValueCtx]:
    target = (l_exp - r_exp).build(block_ctx)

    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.sub(l, r)
    return (
        target,
        Pair.create(res, block_ctx),
    )


@register_context
@rule
def build_icmp_signed(
    l_exp: ValueExpr, r_exp: ValueExpr, operator: str, block_ctx: BlockCtx,
) -> R[ValueCtx]:
    target = l_exp.icmp_signed(operator, r_exp).build(block_ctx)
    l, block_ctx = l_exp.build(block_ctx).spread
    r, block_ctx = r_exp.build(block_ctx).spread
    res = block_ctx.left.icmp_signed(operator, l, r)
    return (
        target,
        Pair.create(res, block_ctx),
    )


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

    return (
        target,
        Pair.create(final_value, block_ctx),
    )


@register_context
@rule
def build_constant(value: Value, block_ctx: BlockCtx) -> R[ValueCtx]:
    return (
        ValueExpr.from_value(value).build(block_ctx),
        Pair.create(value, block_ctx),
    )


import metadsl_core as mc
import metadsl_llvm as ml


__all__ = ["create_metadsl_fn"]

def create_metadsl_fn():
    # Constants
    int_type = ml.Type.create_int(32)
    zero = ml.Value.constant(int_type, 0)
    one = ml.Value.constant(int_type, 1)

    # Module reference
    mod_ref = ml.ModuleReference.create("fib")

    # Module builder
    mod_builder = ml.ModuleBuilder.create(mod_ref)

    # Function references

    mod_builder, fib_more_ref = ml.FunctionReference.create(
        mod_builder,
        ml.FunctionType.create(int_type, int_type, int_type, int_type),
        "fib_more",
        "fastcc",
    ).spread

    mod_builder, fib_ref = ml.FunctionReference.create(
        mod_builder, ml.FunctionType.create(int_type, int_type), "fib", "fastcc"
    ).spread

    # Function builders
    fib_more_builder = ml.FunctionBuilder.create(fib_more_ref)
    fib_builder = ml.FunctionBuilder.create(fib_ref)

    # Function args
    fib_n = fib_more_builder.arguments[mc.Integer.from_int(0)]

    fib_more_n = fib_builder.arguments[mc.Integer.from_int(0)]
    fib_more_a = fib_builder.arguments[mc.Integer.from_int(1)]
    fib_more_b = fib_builder.arguments[mc.Integer.from_int(2)]

    # Block references
    fib_more_builder, fib_more_entry_ref = ml.BlockReference.create(
        "entry", fib_more_builder
    ).spread
    fib_more_builder, fib_more_pred_cont_ref = ml.BlockReference.create(
        "pred_cont", fib_more_builder
    ).spread
    fib_more_builder, fib_more_not_pred_cont_ref = ml.BlockReference.create(
        "not_pred_cont", fib_more_builder
    ).spread
    fib_more_builder, fib_more_n_eq_one_ref = ml.BlockReference.create(
        "n_eq_one", fib_more_builder
    ).spread
    fib_more_builder, fib_more_n_neq_one_ref = ml.BlockReference.create(
        "n_neq_one", fib_more_builder
    ).spread

    fib_builder, fib_entry_ref = ml.BlockReference.create("entry", fib_builder).spread

    # Block builders

    fib_more_entry_builder = ml.Builder.create(fib_more_entry_ref)
    fib_more_pred_cont_builder = ml.Builder.create(fib_more_pred_cont_ref)
    fib_more_not_pred_cont_builder = ml.Builder.create(fib_more_not_pred_cont_ref)
    fib_more_n_eq_one_builder = ml.Builder.create(fib_more_n_eq_one_ref)
    fib_more_n_neq_one_builder = ml.Builder.create(fib_more_n_neq_one_ref)

    fib_entry_builder = ml.BlockBuilder.create(fib_entry_ref)

    # Values

    fib_entry_builder, fib_entry_value = fib_entry_builder.call(
        fib_more_ref, mc.Vec.create(fib_n, zero, one)
    ).spread
    fib_entry_builder = fib_entry_builder.ret(fib_entry_value)

    fib_more_entry_builder, pred_cont = fib_more_entry_builder.icmp_signed(
        ">", fib_more_n, one
    ).spread
    fib_more_entry_builder = fib_more_entry_builder.cbranch(
        pred_cont, fib_more_pred_cont_ref, fib_more_not_pred_cont_ref
    )

    fib_more_pred_cont_builder, minus1 = fib_more_pred_cont_builder.sub(
        fib_more_n, one
    ).spread
    fib_more_pred_cont_builder, ab = fib_more_pred_cont_builder.add(
        fib_more_a, fib_more_b
    )
    fib_more_pred_cont_builder, added = fib_more_pred_cont_builder.call(
        fib_more_ref, mc.Vec.create(minus1, fib_more_b, ab)
    ).spread
    fib_more_pred_cont_builder = fib_more_pred_cont_builder.ret(added)

    fib_more_not_pred_cont_builder, n_eq_1 = fib_more_not_pred_cont_builder.icmp_signed(
        "==", fib_more_n, one
    )
    fib_more_not_pred_cont_builder = fib_more_not_pred_cont_builder.cbranch(
        n_eq_1, fib_more_n_eq_one_ref, fib_more_n_neq_one_ref
    )

    fib_more_n_eq_one_builder = fib_more_n_eq_one_builder.ret(fib_more_b)

    fib_more_n_neq_one_builder = fib_more_n_neq_one_builder.ret(fib_more_a)

    # Blocks
    fib_more_entry_block = ml.Block.create(fib_more_entry_ref, fib_more_entry_builder)
    fib_more_pred_cont_block = ml.Block.create(
        fib_more_pred_cont_ref, fib_more_pred_cont_builder
    )
    fib_more_not_pred_cont_block = ml.Block.create(
        fib_more_not_pred_cont_ref, fib_more_not_pred_cont_builder
    )
    fib_more_n_eq_one_block = ml.Block.create(
        fib_more_n_eq_one_ref, fib_more_n_eq_one_builder
    )
    fib_more_n_neq_one_block = ml.Block.create(
        fib_more_n_neq_one_ref, fib_more_n_neq_one_builder
    )

    fib_entry_block = ml.Block.create(fib_entry_ref, fib_entry_builder)

    # Functions
    fib_more_fn = ml.Function.create(
        fib_more_ref,
        mc.Vec.create(
            fib_more_entry_block,
            fib_more_pred_cont_block,
            fib_more_not_pred_cont_block,
            fib_more_n_eq_one_block,
            fib_more_n_neq_one_block,
        ),
    )

    fib_fn = ml.Function.create(fib_ref, mc.Vec.create(fib_entry_block))

    # Module

    module = ml.Module.create(mod_ref, mc.Vec.create(fib_fn, fib_more_fn))

    c_int = ml.CType.c_int()
    c_func_type = ml.CFunctionType.create(c_int, c_int)

    return ml.compile_function(module, mod_builder, fib_ref, c_func_type)

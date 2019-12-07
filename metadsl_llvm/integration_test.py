import metadsl as m
import metadsl_core as mc
import metadsl_llvm as ml


def test_fib():

    ##
    # Constants
    ##

    int_type = ml.Type.create_int(32)
    zero = ml.Value.constant(int_type, 0)
    one = ml.Value.constant(int_type, 1)

    ##
    # Module Builder
    ##
    mod_builder = ml.ModuleBuilder.create("fib")

    ##
    # Function Builders
    ##
    mod_builder, fib_more_builder = ml.FunctionBuilder.create(
        mod_builder,
        ml.FunctionType.create(int_type, int_type, int_type, int_type),
        "fib_more",
        "fastcc",
    ).spread

    mod_builder, fib_fn_builder = ml.FunctionBuilder.create(
        mod_builder, ml.FunctionType.create(int_type, int_type), "fib", "fastcc"
    ).spread

    ##
    # Arguments
    ##

    fib_n = fib_fn_builder.arguments[mc.Integer.from_int(0)]
    fib_more_n = fib_more_builder.arguments[mc.Integer.from_int(0)]
    fib_more_a = fib_more_builder.arguments[mc.Integer.from_int(1)]
    fib_more_b = fib_more_builder.arguments[mc.Integer.from_int(2)]

    ##
    # Block Builders
    ##
    fib_fn_builder, fib_entry_builder = ml.BlockBuilder.create(
        "entry", fib_fn_builder
    ).spread
    fib_more_builder, fib_more_entry_builder = ml.BlockBuilder.create(
        "entry", fib_more_builder
    ).spread
    fib_more_builder, fib_pred_cont_builder = ml.BlockBuilder.create(
        "pred_cont", fib_more_builder
    ).spread
    fib_more_builder, fib_not_pred_cont_builder = ml.BlockBuilder.create(
        "not_pred_cont", fib_more_builder
    ).spread
    fib_more_builder, fib_n_eq_one_builder = ml.BlockBuilder.create(
        "n_eq_one", fib_more_builder
    ).spread
    fib_more_builder, fib_n_neq_one_builder = ml.BlockBuilder.create(
        "n_neq_one", fib_more_builder
    ).spread

    ##
    # Values
    ##

    fib_entry_builder, fib_entry_res = fib_entry_builder.call(
        fib_more_builder, mc.Vec.create(fib_n, zero, one)
    ).spread
    fib_entry_builder = fib_entry_builder.ret(fib_entry_res)

    fib_more_entry_builder, pred_cont = fib_more_entry_builder.icmp_signed(
        ">", fib_more_n, one
    ).spread

    fib_more_entry_builder = fib_more_entry_builder.cbranch(
        pred_cont, fib_pred_cont_builder, fib_not_pred_cont_builder
    )

    fib_pred_cont_builder, minus1 = fib_pred_cont_builder.sub(fib_more_n, one).spread
    fib_pred_cont_builder, ab = fib_pred_cont_builder.add(fib_more_a, fib_more_b).spread

    fib_pred_cont_builder, added = fib_pred_cont_builder.call(
        fib_more_builder, mc.Vec.create(minus1, fib_more_b, ab)
    ).spread
    fib_pred_cont_builder = fib_pred_cont_builder.ret(added)

    fib_not_pred_cont_builder, n_eq_1 = fib_not_pred_cont_builder.icmp_signed(
        "==", fib_more_n, one
    ).spread
    fib_not_pred_cont_builder = fib_not_pred_cont_builder.cbranch(
        n_eq_1, fib_n_eq_one_builder, fib_n_neq_one_builder
    )

    fib_n_eq_one_builder = fib_n_eq_one_builder.ret(fib_more_b)

    fib_n_neq_one_builder = fib_n_neq_one_builder.ret(fib_more_a)

    ##
    # Functions
    ##
    fib_fn_real = ml.Function.create(fib_fn_builder, mc.Vec.create(fib_entry_builder))
    fib_more_fn_real = ml.Function.create(
        fib_more_builder,
        mc.Vec.create(
            fib_more_entry_builder,
            fib_pred_cont_builder,
            fib_not_pred_cont_builder,
            fib_n_eq_one_builder,
            fib_n_neq_one_builder,
        ),
    )

    ##
    # Module
    ##

    module_real = ml.Module.create(
        mod_builder, mc.Vec.create(fib_fn_real, fib_more_fn_real)
    )

    ##
    # CType
    ##
    c_int = ml.CType.c_int()
    c_func_type = ml.CFunctionType.create(c_int, c_int)

    metadsl_fn = m.execute(
        ml.compile_function(module_real, mod_builder, fib_fn_builder, c_func_type)
    )
    assert metadsl_fn(10) == 55


def test_add():
    ##
    # Constants
    ##

    int_type = ml.Type.create_int(32)
    one = ml.Value.constant(int_type, 1)

    mod_builder = ml.ModuleBuilder.create("add")
    mod_builder, fn_builder = ml.FunctionBuilder.create(
        mod_builder,
        ml.FunctionType.create(int_type, int_type, int_type),
        "add",
        "fastcc",
    ).spread

    l = fn_builder.arguments[mc.Integer.from_int(0)]
    r = fn_builder.arguments[mc.Integer.from_int(1)]

    function_builder, block_builder = ml.BlockBuilder.create("entry", fn_builder).spread
    block_builder, lr = block_builder.add(l, r).spread
    block_builder, res = block_builder.add(lr, one).spread
    block_builder = block_builder.ret(res)

    ##
    # Functions
    ##
    fn = ml.Function.create(fn_builder, mc.Vec.create(block_builder))

    ##
    # Module
    ##

    mod = ml.Module.create(mod_builder, mc.Vec.create(fn))

    ##
    # CType
    ##
    c_int = ml.CType.c_int()
    c_func_type = ml.CFunctionType.create(c_int, c_int)

    real_fn = m.execute(ml.compile_function(mod, mod_builder, fn_builder, c_func_type))
    assert real_fn(10) == 21

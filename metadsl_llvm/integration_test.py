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
    # Module Ref
    ##
    mod_ref = ml.ModRef.create("fib")

    ##
    # Function Refs
    ##
    fib_more_ref = mod_ref.function(
        "fib_more", ml.FnType.create(int_type, int_type, int_type, int_type), "fastcc",
    )

    fib_ref = mod_ref.function("fib", ml.FnType.create(int_type, int_type), "fastcc")

    ##
    # Arguments
    ##

    fib_n = fib_ref.arguments[mc.Integer.from_int(0)]
    fib_more_n = fib_more_ref.arguments[mc.Integer.from_int(0)]
    fib_more_a = fib_more_ref.arguments[mc.Integer.from_int(1)]
    fib_more_b = fib_more_ref.arguments[mc.Integer.from_int(2)]

    ##
    # Block Refs
    ##
    fib_entry = fib_ref.block(True, "entry")
    fib_more_entry = fib_more_ref.block(True, "entry")
    fib_more_pred_cont = fib_more_ref.block(False, "pred_cont")
    fib_more_not_pred_cont = fib_more_ref.block(False, "not_pred_cont")
    fib_more_n_eq_one = fib_more_ref.block(False, "n_eq_one")
    fib_more_n_neq_one = fib_more_ref.block(False, "n_neq_one")

    ##
    # Values
    ##

    fib_entry_terminate = fib_entry.ret(
        fib_entry.call(fib_more_ref, mc.Vec.create(fib_n, zero, one))
    )

    fib_more_entry_terminate = fib_more_entry.cbranch(
        fib_more_entry.icmp_signed(">", fib_more_n, one),
        fib_more_pred_cont,
        fib_more_not_pred_cont,
    )

    fib_more_pred_cont_terminate = fib_more_pred_cont.ret(
        fib_more_pred_cont.call(
            fib_more_ref,
            mc.Vec.create(
                fib_more_pred_cont.sub(fib_more_n, one),
                fib_more_b,
                fib_more_pred_cont.add(fib_more_a, fib_more_b),
            ),
        )
    )

    fib_more_not_pred_cont_terminate = fib_more_not_pred_cont.cbranch(
        fib_more_not_pred_cont.icmp_signed("==", fib_more_n, one),
        fib_more_n_eq_one,
        fib_more_n_neq_one,
    )

    fib_more_n_eq_one_terminate = fib_more_n_eq_one.ret(fib_more_b)

    fib_more_n_neq_one_terminate = fib_more_n_eq_one.ret(fib_more_a)

    ##
    # Functions
    ##
    fib_fn = ml.Fn.create(mc.Vec.create(fib_entry_terminate))
    fib_more_fn = ml.Fn.create(
        mc.Vec.create(
            fib_more_entry_terminate,
            fib_more_pred_cont_terminate,
            fib_more_not_pred_cont_terminate,
            fib_more_n_eq_one_terminate,
            fib_more_n_neq_one_terminate,
        ),
    )

    ##
    # Module
    ##

    mod = ml.Mod.create(mc.Vec.create(fib_fn, fib_more_fn))

    ##
    # CType
    ##
    c_int = ml.CType.c_int()
    c_func_type = ml.CFunctionType.create(c_int, c_int)

    metadsl_fn = m.execute(ml.compile_function(mod, mod_ref, fib_ref, c_func_type))
    assert metadsl_fn(10) == 55


def test_add():
    ##
    # Constants
    ##

    int_type = ml.Type.create_int(32)
    one = ml.Value.constant(int_type, 1)

    mod_ref = ml.ModRef.create("add")
    fn_ref = mod_ref.function(
        "add", ml.FnType.create(int_type, int_type, int_type), "fastcc",
    )

    l = fn_ref.arguments[mc.Integer.from_int(0)]
    r = fn_ref.arguments[mc.Integer.from_int(1)]

    block_ref = fn_ref.block(True)
    lr = block_ref.add(l, r)
    res = block_ref.add(lr, one)
    terminate = block_ref.ret(res)

    fn = ml.Fn.create(mc.Vec.create(terminate))

    mod = ml.Mod.create(mc.Vec.create(fn))

    c_int = ml.CType.c_int()
    c_func_type = ml.CFunctionType.create(c_int, c_int)

    real_fn = m.execute(ml.compile_function(mod, mod_ref, fn_ref, c_func_type))
    assert real_fn(10) == 21

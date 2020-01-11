import metadsl as m
import metadsl_core as mc
import metadsl_llvm as ml


def test_fib():
    ##
    # Constants
    ##

    int_type = ml.Type.create_int(32)
    zero = ml.ValueExpr.from_value(ml.Value.constant(int_type, 0))
    one = ml.ValueExpr.from_value(ml.Value.constant(int_type, 1))

    ##
    # Module
    ##
    mod_ref = ml.ModRef.create("fib")
    mod_expr = ml.ModExpr.from_mod_ref(mod_ref)

    @mod_expr.fn_dec(ml.FnType.create(int_type, int_type, int_type, int_type))
    @mc.FunctionThree.from_fn
    def fib_more(n: ml.ValueExpr, a: ml.ValueExpr, b: ml.ValueExpr) -> ml.ValueExpr:
        return (n > one).if_(fib_more(n - one, b, a + b), (n.eq(one).if_(b, a)))

    @mod_expr.fn_dec(ml.FnType.create(int_type, int_type))
    @mc.FunctionOne.from_fn
    def fib(n: ml.ValueExpr) -> ml.ValueExpr:
        return fib_more(zero, one)

    metadsl_fn = m.execute(fib.compile(mod_ref, fib_more))
    assert metadsl_fn(10) == 55


def test_add():
    int_type = ml.Type.create_int(32)
    one = ml.ValueExpr.from_value(ml.Value.constant(int_type, 1))

    mod_ref = ml.ModRef.create("add")
    mod_expr = ml.ModExpr.from_mod_ref(mod_ref)

    @mod_expr.fn_dec(ml.FnType.create(int_type, int_type, int_type))
    @mc.FunctionTwo.from_fn
    def add(l: ml.ValueExpr, r: ml.ValueExpr) -> ml.ValueExpr:
        return l + r + one

    real_fn = m.execute(add.compile(mod_ref))
    assert real_fn(10, 11) == 22

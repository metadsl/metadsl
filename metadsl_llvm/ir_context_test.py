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

    @ml.llvm_fn(mod_ref, ml.FnType.create(int_type, int_type, int_type, int_type))
    @mc.FunctionThree.from_fn_recursive
    def fib_more(
        self: mc.FunctionThree[ml.ValueExpr, ml.ValueExpr, ml.ValueExpr, ml.ValueExpr],
        n: ml.ValueExpr,
        a: ml.ValueExpr,
        b: ml.ValueExpr,
    ) -> ml.ValueExpr:
        return (n > one).if_(self(n - one, b, a + b), (n.eq(one).if_(b, a)))

    @ml.llvm_fn(mod_ref, ml.FnType.create(int_type, int_type))
    @mc.FunctionOne.from_fn
    def fib(n: ml.ValueExpr) -> ml.ValueExpr:
        return fib_more(n, zero, one)

    metadsl_fn = m.execute(
        ml.compile_functions(mod_ref, ml.to_llvm(fib), ml.to_llvm(fib_more))
    )
    assert metadsl_fn(10) == 55


def test_add():
    int_type = ml.Type.create_int(32)
    one = ml.ValueExpr.from_value(ml.Value.constant(int_type, 1))

    mod_ref = ml.ModRef.create("add")

    @ml.llvm_fn(mod_ref, ml.FnType.create(int_type, int_type, int_type))
    @mc.FunctionTwo.from_fn
    def add(l: ml.ValueExpr, r: ml.ValueExpr) -> ml.ValueExpr:
        return l + r + one

    real_fn = m.execute(ml.compile_functions(mod_ref, ml.to_llvm(add)))
    assert real_fn(10, 11) == 22

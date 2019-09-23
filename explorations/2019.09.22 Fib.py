#!/usr/bin/env python
# coding: utf-8

# # Fibonnaci
# 
# In this notebook we will show a few different ways of compiling the fibonnaci functon with LLVM in Python.
# 
# This is inspired by [Siu's work](https://github.com/sklam/etude-okvmap/blob/1e85c5ea7bb1f092ed251159e7046d1348f3fa8b/example_minilang.py#L285-L300) as an attempt to explore how metadsl could be useful as a way to build higher level expression systems on top of LLVM in Python.

# ## `llvmlite`
# 
# First, lets start with the low level `llvmlite` library to build up the llvm directly:

# In[2]:


import faulthandler
faulthandler.enable()

from llvmlite import ir

def create_mod():
    mod = ir.Module(name="fib")

    int_type = ir.IntType(32)
    zero = ir.Constant(int_type, 0)
    one = ir.Constant(int_type, 1)

    fib_more_fn = ir.Function(
        mod,
        ir.FunctionType(int_type, [int_type, int_type, int_type]),
        name='fib_more',
    )
    
    fib_fn = ir.Function(
        mod,
        ir.FunctionType(int_type, [int_type]),
        name='fib'
    )
    
    fib_fn.calling_convention = 'fastcc'
    fib_more_fn.calling_convention = 'fastcc'


    fib_n, = fib_fn.args
    fib_more_n, fib_more_a, fib_more_b = fib_more_fn.args


    fib_entry = fib_fn.append_basic_block('entry')
    fib_more_entry = fib_more_fn.append_basic_block('entry')
    fib_pred_cont = fib_more_fn.append_basic_block('pred_cont')
    fib_not_pred_cont = fib_more_fn.append_basic_block('not_pred_cont')
    fib_n_eq_one = fib_more_fn.append_basic_block('n_eq_one')
    fib_n_neq_one = fib_more_fn.append_basic_block('n_neq_one')

    fib_entry_builder = ir.IRBuilder(fib_entry)
    fib_more_entry_builder = ir.IRBuilder(fib_more_entry)
    fib_pred_cont_builder = ir.IRBuilder(fib_pred_cont)
    fib_not_pred_cont_builder = ir.IRBuilder(fib_not_pred_cont)
    fib_n_eq_one_builder = ir.IRBuilder(fib_n_eq_one)
    fib_n_neq_one_builder = ir.IRBuilder(fib_n_neq_one)


    fib_entry_builder.ret(
        fib_entry_builder.call(
            fib_more_fn,
            (fib_n, zero, one)
        )
    )


    pred_cont = fib_more_entry_builder.icmp_signed(">", fib_more_n, one)
    minus1 = fib_more_entry_builder.sub(fib_more_n, one)
    ab = fib_more_entry_builder.add(fib_more_a, fib_more_b)
    added = fib_more_entry_builder.call(fib_more_fn, (minus1, fib_more_b, ab))

    n_eq_1 = fib_more_entry_builder.icmp_signed("==", fib_more_n, one)

    fib_more_entry_builder.cbranch(pred_cont, fib_pred_cont, fib_not_pred_cont)

    fib_pred_cont_builder.ret(added)

    fib_not_pred_cont_builder.cbranch(n_eq_1, fib_n_eq_one, fib_n_neq_one)

    fib_n_eq_one_builder.ret(fib_more_b)

    fib_n_neq_one_builder.ret(fib_more_a)

    return mod

llvm_ir = (str(create_mod()))
print(llvm_ir)


# In[ ]:


from ctypes import CFUNCTYPE, c_int
from llvmlite import binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


def execute(llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    llmod = llvm.parse_assembly(llvm_ir)
    llmod.verify()
    
    # Now add the module and make sure it is ready for execution
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 1
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(llmod)

    target_machine = llvm.Target.from_default_triple().create_target_machine()

    with llvm.create_mcjit_compiler(llmod, target_machine) as ee:
        ee.finalize_object()
        cfptr = ee.get_function_address("fib")

        cfunc = CFUNCTYPE(c_int, c_int)(cfptr)

        # TEST
        for i in range(12):
            res = cfunc(i)
            print('fib({}) = {}'.format(i, res))

        # Get CFG
        ll_fib_more = llmod.get_function('fib_more')
        cfg = llvm.get_function_cfg(ll_fib_more)
        llvm.view_dot_graph(cfg, view=True)
execute(llvm_ir)


# In[ ]:





#!/usr/bin/env python
# coding: utf-8

# # Fibonnaci
# 
# In this notebook we will show a few different ways of compiling the fibonnaci functon with LLVM in Python.
# 
# This is inspired by [Siu's work](https://github.com/sklam/etude-okvmap/blob/1e85c5ea7bb1f092ed251159e7046d1348f3fa8b/example_minilang.py#L285-L300) as an attempt to explore how metadsl could be useful as a way to build higher level expression systems on top of LLVM in Python.

# ## Pure Python
# 
# First, lets create a pure python version

# In[1]:


N = 1000


# In[2]:


def fib_more(n, a, b):
    if n > 1:
        return fib_more(n - 1, b, a + b)
    if b == 1:
        return b
    return a

def fib(n):
    return fib_more(n, 0, 1)


# In[3]:


# %timeit fib(N)


# ## `llvmlite`
# 
# First, lets start with the low level `llvmlite` library to build up the llvm directly:

# In[6]:


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


    fib_more_entry_builder.cbranch(pred_cont, fib_pred_cont, fib_not_pred_cont)
    
    minus1 = fib_pred_cont_builder.sub(fib_more_n, one)
    ab = fib_pred_cont_builder.add(fib_more_a, fib_more_b)
    added = fib_pred_cont_builder.call(fib_more_fn, (minus1, fib_more_b, ab))
    fib_pred_cont_builder.ret(added)

    n_eq_1 = fib_not_pred_cont_builder.icmp_signed("==", fib_more_n, one)
    fib_not_pred_cont_builder.cbranch(n_eq_1, fib_n_eq_one, fib_n_neq_one)

    fib_n_eq_one_builder.ret(fib_more_b)

    fib_n_neq_one_builder.ret(fib_more_a)

    return mod

llvm_ir = (str(create_mod()))
# print(llvm_ir)


# In[5]:


from ctypes import CFUNCTYPE, c_int
from llvmlite import binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

def make_c_wrapper(fn_callee):
    mod = fn_callee.module
    fnty = fn_callee.function_type
    fn = ir.Function(mod, fnty, name='entry_' + fn_callee.name)
    builder = ir.IRBuilder(fn.append_basic_block())
    builder.ret(builder.call(fn_callee, fn.args))



def execute(llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    llmod = llvm.parse_assembly(str(llvm_ir))
    llmod.verify()
    
#     print('optimized'.center(80, '-'))
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 1
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(llmod)
#     print(llmod)

    target_machine = llvm.Target.from_default_triple().create_target_machine()

    ee = llvm.create_mcjit_compiler(llmod, target_machine)
    ee.finalize_object()
    cfptr = ee.get_function_address("entry_fib")

    cfunc = CFUNCTYPE(c_int, c_int)(cfptr)
    return ee, cfunc

    # Get CFG
#         ll_fib_more = llmod.get_function('fib_more')
#         cfg = llvm.get_function_cfg(ll_fib_more)
#         llvm.view_dot_graph(cfg, view=True)

mod = create_mod()
make_c_wrapper(mod.get_global('fib'))
_, f = execute(mod)


# In[6]:


# %timeit f(N)


# We see this is two orders of magnitude faster than the Python code, partially because we are closer to the metal and partially because LLVM turns this tail recursion into a loop.

# ## `metadsl` with `llvmlite` wrapper

# In[1]:


import metadsl as m
import metadsl_core as mc
import metadsl_llvm as ml
import metadsl_visualize


# In[17]:



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


# In[18]:


metadsl_fn = m.execute(create_metadsl_fn())


# In[ ]:





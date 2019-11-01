#!/usr/bin/env python
# coding: utf-8

# In[1]:


from metadsl import *
from metadsl_core import *
from metadsl_llvm.pure import *

import metadsl_visualize

import typez
typez.SHOW_TYPES = False

# Disable fixed point expansion temporarily
run_post_rules(False)


# In[2]:


one = Integer.from_int(1)
zero = Integer.from_int(0)


# In[3]:


mod = Module.create("Main")

@FunctionThree.from_fn_recursive
def fib_more(
    fn: FunctionThree[Integer, Integer, Integer, Integer],
    n: Integer,
    a: Integer,
    b: Integer,
) -> Integer:
    pred_cont = n > one
    minus1 = n - one
    ab = a + b
    added = fn(minus1, b, ab)

    n_eq_1 = n.eq(one)
    return pred_cont.if_(added, n_eq_1.if_(b, a))

res = mod.register_function_three(fib_more)
mod, fib_more_ref = res.left(), res.right()

@FunctionOne.from_fn
def fib(n: Integer) -> Integer:
    return fib_more_ref(n, zero, one)


mod.register_function_one(fib)._ipython_display_()


# In[ ]:


fib(Integer.from_int(10))


# In[ ]:





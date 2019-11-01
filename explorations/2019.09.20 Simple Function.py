#!/usr/bin/env python
# coding: utf-8

# In[1]:


from metadsl import *
from metadsl_core import *

import metadsl_visualize

import typez
typez.SHOW_TYPES = True


# In[2]:


@FunctionTwo.from_fn
def add(a: Integer, b: Integer) -> Integer:
    return a + b


# In[3]:


res = add(Integer.from_int(1), Integer.from_int(1))


# In[5]:


res._ipython_display_()


# In[ ]:





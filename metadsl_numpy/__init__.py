"""
Array tools built on metadsl

On the user end, we have a Array.

We should be able to do getitem, addition, concat (many arrays with same shape),
and chunk (split it into many arrays with same shape).

It will have a create(shape, idx_fn), shape


We will use a `assertInRange(int, low, hi)` to create bounded integers and do math on those.


We add an ArrayManager class that has a getitem that takes an integer and returns
a np array and has a `persist` method that takes an
array and gives a new one. It will be created with a list of NP arrays
as well as a dict that allows unhashable keys (using equality for testing)
that maps hashes of expression to indexes.  It

It will:

1. splits into chunks of length N
2. Map these arrays with the persist_single function which
   takes the called index fn (with some placeholder) and shape and returns a new array.
3. In a new phase of the replacement, so that the index fn has time to be simplified,
   look it up in the dict. If it's there, replace with the array with `np_array(manager[i])`
   If it's not there, replace with `np_array(manager.save_chunk(arr))`
3. In a new phase replace `manager.save_chunk(arr)` by creating a new empty array, and save it as `manager.saving_chunk(i, *indices)`
   where indices are a indices are a `np_setitem(arr, to_int_tuple(idxs), to_int(value))` which rerturn non


`np_array(x)` translate to `np_getitem(x, to_int_tuple(idxs))`

`manager.saving_chink(i, None, *)` -> `manager.saving_chunk(i, *)`
`manager.saving_chunk(i)` -> `manager[i]`


NO WAIT. I can't generate all these... I must generate ast :(




"""

__version__ = "0.0.0"

from metadsl import export_from

from .bool_compat import *
from .boxing import *
from .function_compat import *
from .injest import *
from .int_compat import *
from .tuple_compat import *

export_from(
    __name__,
    "injest",
    "boxing",
    "bool_compat",
    "int_compat",
    "tuple_compat",
    "function_compat",
)

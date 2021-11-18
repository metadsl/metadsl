"""
# SSA

The goal of this package is to present an alternative representation of Python
that is more amenable to analysis and optimization. It aims to do this by
lifting Python's bytecode into an SSA form and then transforming that SSA
CFG into a dataflow graph.

It mirrors in some way the work in the C / LLVM space to automatically parallize
and optimize that code.

One way we can understand this problem is visually, as the number of differnt
forms Python takes:

1. In the **CPython** implementation, Python goes from:
  1. **Source code**
  2. to an **AST**
  3. to **bytecode**
2. **This package** takes the bytecode level and transforms it to:
  1. a **minimal semantics of the bytecode** level, that is more tightly specified
     than how the bytecode is represented in memory
  2. an **SSA CFG** created from the bytecode. This translation is meant to be an
     abstract analog of CPython's bytecode interpreter. So that instead of 
     interpreting the bytecode eagerly, it builds up a CFG first that has the
     same semantics as interpreting it.
  3. A dataflow graph, showing data dependencies, from this SSA. At this level,
     program optimization becomes much simpler and straightforward.

We test out abstraction level 1-3 by also building ways to go backwards, and
taking Python bytecode as an input and making sure all the transformations are
isomorphic. This type of testing can help us be confident that the different
representations are semantically faithful to the original bytecode source, and
so the original Python behavior.

To use this library to somehow optimize or analyze Python code then, you would
walk down the first three Python levels, then walk down our three levels we
provide here, perform any optimizations or translations, and walk back up
however many levels you like to get the form you are looking for. 

The underlying theory behind this library is that at the dataflow graph level,
we can more closely represent the programs denotional semantics, aka the
underlying conceptual meaning of the program. This is the level closer to our
own human understanding of what the program "does". So if we can move the
program faithfully up to this level, then we can reason about it in terms which
are closer to how we think.

For example, as a human we can reason about adding taking the sum of two
arrays, and say that "the result at index i is the addition of the first array
at index i at the second array at index i. So if we add two arrays and then
immediately index, we know that we don't have to recompute the full array, but
simply the sum of the two corresponding values." Encoding this sort of logic at
the level of Python bytecode simply does not make sense. The bytecode has no
idea about some abstract value of an array, or more fundamentally even of a
value that is defined mathematically like this. However, at the dataflow level,
it becomes feasible to reason about values in this matheamtical sense, instead
of in a memory/imperative sense. So at least we have some hope of being express
this sort of meaning, and have the computer use it to optimize our program.

After doing this optimization,  we can move it back down to whatever level we
like to actually execute. We might chose to go back to Python source, or we
might instead chose to compile to some alternative implementaiton before
executing, such as high level language like SQL or a lower level langauge like
LLVM.
"""


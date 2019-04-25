# Why Metadsl?

## Users Needs

Python data science community wants to continue to collaborate over **shared stable APIs** (NumPy, Pandas, etc.), but want to be able to take advantage of **new optimizations** (like Polyhedral compilation, all the work being done in NN community, simplifying math of arrays (MoA)) and **new hardware/computation environemnts** (GPUs, distributed, end of moores law means more specialized hardware (TPU) needed to keep speed increases).


## Implications

Our current tools (scikit-learn, pandas, xarray) are built on NumPy, which is tied very losely to its computation environment, C/fortran functions over strided arrays.

We need to be able to insert a layer between the API users depend on and how it is executed. This will provide a place for people to innovate on new ways to execute scientific computing, in Python, without requiring users to change how their applications to opt in.

What we are looking for is a pluggable framework that lets us define different APIs, different ways to execute them and convert between them.


Python is known as the "second best language for everything". It is the glue that ties together the different pieces hidden below it. It has worked wonderfully in this way for NumPy, by hiding the complexity of C and Fortran routines and providing them to users in a standard format, so they are not even aware of this complexity.

Now we are asking this glue to go a step further, so instead of saying "I want to execute this piece in C, now give me the result", we are saying "I have composed this sequence of function calls, now go execute all of them as you wish".

By creating a common framework around this, we can share optimizations around common APIs, even if they end up being executed in different contexts. Also, by settling on common ways to express APIs (this meta stucture) then we can enable users to plug and play optimizations, without changing their code.

## Prior work

`ibis` takes a `metadsl` like approach for Pandas, by creating a version of the pandas API that can execute on databases or in memory. `metadsl` is a general framework to build this sort of user facing API and defining the different backends to replace to.

`numba` similarily takes a whole-program approach to executing scientific Python code. I hope that eventually these use cases can overlap, but they have different priorities. It is much easier to extend `metadsl` and create new APIs on it, than in Numba. Numba is tied closely to LLVM and it wouldn't make sense to implement python-to-python translation with it. It can translate control flow though, which metadsl cannot.

`autograph` from Google is similar to Numba, and it is tied somewhat to XLA. I hope to collaborate with these folks on figuring out standard ways of overloading control flow in Python.



## Specific need

We came to this problem by trying to take the ideas in Lenore Mullin's Mathematics of Arrays and make them useful for those in Python.

It isn't hard to implement these concepts in pure Python, but the issue is then then only execute within the CPython runtime and
are rather slow. Numeric computing in Python does not execute in Python, it calls out to other libraries which perform
the low level routines. With Mathematics of Arrays, we generate descriptions of these low level routines dynamically,
based on the mathematical properties of the combined operations.

Much like numba, we needed a way to expres the ideas at a high level in Python, but then have the ability to execute them in
a different environment. So we need to move up one abstraction layer, and create code that represents what we want to execute
instead of executing it directly. Metadsl is meant to be the space to write this kind of representation.



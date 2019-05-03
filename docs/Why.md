# Why does it exist?

`metadsl` comes out of needing to be flexible in how array computing is executed, while giving users a familiar API. We want to be able
to continue innovating as an ecosystem in a way that does not disrupt existing use cases.

We found some interesting work by Lenore Mullin, where [over 30 years ago she formalized the semantics of APL into a Mathematics of Arrays](https://www.researchgate.net/publication/308893116_A_Mathematics_of_Arrays). So we had this
nice theoretical representation for array computation and we wanted to make it accessible for users in Python. It would
allow some optimizations, but the real draw was the ability to express complicated higher order operations in
terms of simpler ones, like looping, indexing, and scalar math.

At the same time, we were seeing this proliferation of array backends in Python, that either
targeted novel hardware, like GPUs, or had new optimizations, like [polyhedral compilation](https://github.com/facebookresearch/TensorComprehensions). Deep learning is driving a lot of momentum in the array compiler space both from academia and industry.

We love Python because it can glue together different technologies while providing a pleasant user experience. Ideally, users
can keep using whatever API they are accustomed, and be able to execute it with different optimizations on different frameworks.
The Mathematics of Arrays can help by reducing the scope a backend needs to support, by replacing more complex operations with simpler ones.

So we didn't set out to build a DSL creation library in Python, it just turned out
to be what we needed to fulfill these requirements. We started by building on top of the
[MatchPy](https://matchpy.readthedocs.io/en/latest/)
library in Python for pattern matching, but after a couple of working versions using that, we found it less complicated
to just build what we needed from the ground up.

It is called `metadsl` and not `array-dsl`, because the core machinery that separates intent from execution is not specific to arrays, and is equally applicable to other compute-intensive domains. For example [`Ibis`](https://www.ibis-project.org/) is a
way to execute SQL queries by using a Pandas like API. `metadsl` is meant to be used to build systems like this that are extensible
and can compose with each other. This will enable innovation on different optimization techniques or backends in a decentralized
manner while providing users a consistent experience. 


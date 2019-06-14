# Roadmap

This is a preliminary roadmap to drive the direction of development here.

We would appreciate any input from the community on what would be useful for them, that could serve
to inform this roadmap.

1. Support initial use case with NumPy API that translates to other backends (more details below)
2. Be able to build up NumPy expression
3. Create simple transformer to turn NumPy expressions into PyTorch AST.

4. Add Mathematics of Array optimizations to the pipeline
5. Translate NumPy API to `llvmlite` calls that build up [`xnd`](https://xnd.io/) computation.

## Prototype of initial NumPy API

The initial use case is in scientific computing, where:

1. You want to use the the APIs you know and love (ex. NumPy).
2. But you want it to execute in a new way (ex. on a GPU or distributed across machines).
3. And you want to optimize a chain of operations before executing (ex. `(x * y)[0]` -> `x[0] * y[0]` / [Mathematics of Arrays](https://paperpile.com/app/p/5de098dd-606d-0124-a25d-db5309f99394)).

Here we lay out an end user API that we can create in `metadsl`.

**This is not implemented yet, but serves to guide development**.

### 1. NumPy API

First build up an expression, using the NumPy compatible API:

```python
import metadsl.numpy.compat as np

x = np.arange(10)
condlist = [x<3, x>5]
choicelist = [x, x**2]
y = np.multiply.outer(np.select(condlist, choicelist), x)
```

### 2. Execute Torch / Tensorflow

Then you can execute it, using torch, optionally printing out the generated sources:

```python
import metadsl.torch

metadsl.torch.execute_numpy(y, print_source=True)
```

Which prints:

```python
import torch

def fn():
    x = torch.arange(10)
    selected = torch.where(x < 3, x, torch.where(x > 5, x ** 2, torch.zeros_like(x)))
    return torch.tensordot(selected, x, dims=0)
```

You can also execute it with TensorFlow:

```python
import metadsl.tensorflow

metadsl.tensorflow.execute_numpy(y, print_source=True)
```

Which prints:

```python
import tensorflow

@tensorflow.function
def fn():
    x = tf.range(10)
    selected = tensorflow.where(x < 3, x, tensorflow.where(x > 5, x ** 2, tensorflow.zeros_like(x)))
    return tensorflow.tensordot(selected, x, axes=0)
```

### 3. Optimize Operations

Finally, you can also execute the operations in an optimized way,
by combing all the operations into one loop, which can help performance in some case.

You can do this for the original NumPy backend:

```python
import metadsl.numpy

metadsl.torch.execute_numpy(y, print_source=True, optimize=True)
```

```python
import numpy

def fn():
    x = numpy.empty((10,10))

    # Or this could produce one loop over all 100 items
    # and calculate index manually and then resahpe
    for i in range(10):
        for j in range(10):
            selected = i if i < 3 else (i ** 2 if i > 5 else 0)
            x[i, j] = selected * j
    return x
```

And we can do this for PyTorch and Tensorflow backends as well:

## Matching System

Currently, the matching system is implemented in Python and is a not very performant or smart. It simply tries each rule against each subexpression and sees if they match, repeatedly.

We also don't have a way to verify that certain rules don't conflict with each other. Currently, if you do this one will just be chosen arbitrarily to match. We would also like to prove the totality of the rules, so that you know if you have covered all of the cases properly for certain expressions.

To implement these types of features we should use the recent pattern matching research ("Non-linear Pattern Matching with Backtracking for Non-free Data Types") and it's overlap with SMT solvers like Z3 ("Set Constraints, Pattern Match Analysis, and SMT"). Eventually we likely want
to let Z3 handle as much matching as possible instead of doing it in Python.

This would also let us optimize the matching rules, so we pre-compile them. Then, when you created an expression, you could have it use some set of precompiled rules so that the matching happens immediately instead of afterwords.

This would get us the best of both worlds, the ability to define replacements in a decentralized manner, and also the ability to have fast execution. This is like the code generation that SymPy can do or MatchPy has started exploring.

# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest)

A framework for creating domain specific language libraries in Python.

The initial use case is in scientific computing, where:

1. You want to use the the APIs you know and love (ex. NumPy).
2. But you want it to execute in a new way (ex. on a GPU or distributed accross machines).
3. And you want to optimize a chain of operations before executing (ex. `(x * y)[0]` -> `x[0] * y[0]` / [Mathematics of Arrays](https://paperpile.com/app/p/5de098dd-606d-0124-a25d-db5309f99394)).


## Example
*This is not implemented yet but is the desired API.*

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

TODO: Add these examples in the same style.


## Guiding Principles

The goal here is to share as much optimization and representation logic as possible, so that the world users
exist in can be extended more easily without having to cause them to change their code.

For example, if someone comes up with a new way of executing linear algebra or wants to try out a new way of optimizing
expressions, they should be able to write those things in a pluggable manner, so that users can try them out with minimal
effort. 

This means we have to explicitly expose the protocols of the different levels to foster distributed collaboration and reuse. 

## [Roadmap](./ROADMAP.md)

## Development

Either use repo2docker:

```bash
repo2docker -E .
```


Or get started with Conda/flit:

```bash
conda create -n metadsl jupyterlab
conda activate metadsl
pip install flit
flit install --symlink
```

### Tests

This runs mypy and tests, and reports coverage.
```bash
pytest
# open coverage file
open htmlcov/index.html
```


### Docs

```bash
cd docs/
# build
make html
# serve
python -m http.server -d _build/html/
```

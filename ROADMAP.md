# Roadmap

This is a preliminary roadmap to drive the direction of development here. 

We would appreciate any input from the community on what would be useful for them, that could serve
to inform this roadmap.

1. Add examples in docs for low level usage
  1. Create  API for doing arithmetic (adding/multipling numbers)
    1. Show how to write translater that does partial evaluation
    2. Show how to write compiler to Python AST
    3. Add variables and show how these show up in Python AST
    4. Show how to create wrapped version that deals with implicit conversion with python types
  2. Create typed lambda calculus API
    1. Show how to convert between [De Bruijn index](https://en.wikipedia.org/wiki/De_Bruijn_index) and named variable
    2. Show how to implement [Church numerals](https://en.wikipedia.org/wiki/Church_encoding#Church_numerals)
       and arithmatic on top of it
    3. Show how to convert between these and python integers
   
2. Support initial use case with NumPy API that translates to other backends (more details below)
  1. Be able to build up NumPy expression
  2. Create simple transformer to turn numpy expressions into pytorch AST.


## Prototype of initial NumPy API
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

# A New Base


Let's try to recreate metadsl from the ground up here.

## Advantages of metadsl
What are the advantages of this sort of system over operator overloading or dunder methods for
iteropability?

1. Allows anyone to define new operations on datatypes.
2. Allows anyone else to define how those operations before on their underlying representation.

By splitting these things we can easily distribute a "NumPy" that users can depend on
and make that seperate from any implementations.


## Why recreate?
Why do we need to recreate metadsl?


### Add built in types

Because the existing implementation doesn't have any *built in types*. Every types is basically
user defined. Even functions! Or it's a native python type. So currently we have two types of types:

1. User defined types (can be parametric)
2. Foriegn types (native python values)

And we would like to expand it add a third type:

3. Built in types (functions, lists, tuples, dictionaries, etc.)

Why make these built in? Because then we can hard code in coercion and typing rules for these.
For example currently, the way we get functions in metadsl causes a bunch of issues with type variable
binding, due to the lazy nature. (I could go into these but not sure if anyone is interested, if you are we can
just talk).

### Support mutabilitly and multiple return types

The other thing we wanna do is add the ability for functions to mutate their args and return multiple return types.
We can actually do this still by building up a dataflow graph.


## Representation


So how do we represent all this?


```python
from dataclasses import dataclass, field
from typing import *


@dataclass
class Expression:
    __function__: Callable
    __args__: List[Any] = field(default_factory=list)
    __kwargs__: Dict[str, Any] = field(default_factory=dict)
    __typevars__: Dict[str, ]
    # By default, this is None, meaning that this expressiion
    # is the return value of the function.
    # If instead, it is a tuple of ('param', k)
    # then this means it's the resulting state of the param name `k`.
    # Meaning that this function mutates that parameter
    # If it is a tuple of ('return', i) it means it's the ith
    # return value (the function returns a tuple of values)
    __position__: Union[
        None,
        Tuple[Literal['param'], str],
        Typle[Literal['return'], int]
    ] = field(None)
```

We also need some way "injecting" native python types into our system so that then we can
do lazy computations on them.

```python
import functools

T = TypeVar("T")


@functools.singledispatch
def injest(val: T, tp: Optional[Type[T]]) -> T:
    return val

T_list = TypeVar("T_list", bound=list)
@injest.register
def _injest_list(val: T_list, tp: Optional[Type[T_list]]) -> T_list:
    if tp:
        inner_tp = get_inner_tp(tp)
        
        return List[inner_tp].create()
```

Here is an example

```python
>>> l = injest([1, 2, 3])
>>> str(l)
[1, 2, 3]
>>> repr(l)
PyList(PyList.create, [1, 2, 3])
>>> l.append(10)
>>> str(l)
x = [1, 2, 3]
x.append(10)
x
>>> repr(l)
PyList(PyList.append, [PyList(create_list, [1, 2, 3]), 10], {}, ('param', 'self'))
```

```python
list(1, 2, 3)
```

Open question:


Do I have a custom List expression? --> Yes
Then I need some way of converting between "python types" and injested types? --> Yes
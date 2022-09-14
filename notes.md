
## data types
Difference between Using constructors for a union versus a type with a match?

It's really cumbersome to construct data types... See Args for code data. Have to test
each accessor, and duplicate them, obscures meaning.

**Can we use datatypes instead? Frozen ones?** Do we translate to expressions or do
we just keep them as is and add another core type? 

Maybe just treat them as macro. it's just how do we reference function of each property
then, since they are no longer actually properties but just attrbutes?

We could add properties to the class, hm....

---

Maybe Try to support it, without support for generics.

So:

```python
@dataclass
class A(Expression):
    a: int
    b: str
```

Would translate to...
Darn need type level translations!

We currently don't support `__init__` typings, but we could get around that. The main problem is we don't support mutations...

Gosh is there another way we could do it?

Add easier support for dataclasses, to create accessors and getters?

OK so what if we do something like:

```python
class A(Expression, auto=some_strategy):
    @classmethod
    def create(cls, a: int, b: str) -> A:
        ...

    @property
    def a(self) -> int:
        ...
    
    @property
    def b(self) -> str:
        ...
    
    def set_a(self, a: int) -> A:
        ...
    
    def set_b(self, b: str) -> A:
        ...
```

Too much magic with auto creating expression. Instead make it seperate, like this:


```python
class A(Expression):
    @expression
    @classmethod
    def create(cls, a: int, b: str) -> A:
        ...

    @expression
    @property
    def a(self) -> int:
        ...
    
    @expression
    @property
    def b(self) -> str:
        ...
    
    @expression
    def set_a(self, a: int) -> A:
        ...
    
    @expression
    def set_b(self, b: str) -> A:
        ...

register(datatype_rule(A))
```

Which creates into:

```python
class A(Expression):
    @expression
    @classmethod
    def create(cls, a: int, b: str) -> A:
        ...

    @expression
    @property
    def a(self) -> int:
        ...
    
    @expression
    @property
    def b(self) -> str:
        ...
    
    @expression
    def set_a(self, a: int) -> A:
        ...
    
    @expression
    def set_b(self, b: str) -> A:
        ...

@register
@rule
def a_datatype_rule():
    yield A.create(a, b).a, a
    yield A.create(a, b).b, b
    yield A.create(a, b).set_a(a2), A.create(a2, b)
    yield A.create(a, b).set_b(b2), A.create(a, b2)
```

We could also add a `wrap_methods` decorator to turn all methods into expresions,
to remove the noise for the `@expression` decorator.

## Maybe types
How should I type things with error return types? Should they be a maybe type? How should the traceback
be preserved?

For now just lets assert they never error...


## Rules
Can we use matching rules in definitions to make it easier to write rules instead
of having to write them seperately from the def?

## Built in python types

Somtimes it would be easier just to use builtin Python types, like the code type or CodeData... That we don't have to wrap them to provide assessors and such things...

Would also address needs of Dask group partially, to wrap existing functionality...

Would definately open things up a lot! Could use this library then in place with existing APIs, without rewriting them.

Some questions it would bring up:
* How much of Python's type system do we support? Do we support inheritence?
* How do we support things like accessing properties? Do we dissalow all mutations?
* Do we allow untyped objects? Or do we try to pick up typings from PYI files? 

Maybe the data type support would atleast help here..
## data types ✅

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

## Enums

Since we support products, the twin is the enum.

Really, these are product/sum types. Maybe we should rename them to that to be clear.

The superset is [the ADT](https://en.wikipedia.org/wiki/Algebraic_data_type#Theory), which is:

> A general algebraic data type is a possibly recursive sum type of product types.

Options?

1. Make an enum/sum type. How many params per part? Maybe 1 or 1, not more? And for the match
   for those with 1 param, require an abstraction, with 0, just a value?
2. Can we rely on a lower level type language to construct these and map them to Python?

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

- How much of Python's type system do we support? Do we support inheritence?
- How do we support things like accessing properties? Do we dissalow all mutations?
- Do we allow untyped objects? Or do we try to pick up typings from PYI files?

Maybe the data type support would atleast help here..

## Recursive types

We currently don't support recursive types. MyPy [now supports them](https://github.com/python/mypy/issues/731#issuecomment-1260976955)
so we should try doing that too!

## Type DSL

It would be helpful to have a DSL for representing our types, to aid in the type calculations.
Currently, things like `Optional[T]` are not working as type definitions unfortunately...

Would need to have some sort of type abstractions for typevars, and deal with that binding...

### Don't use builtin python types

If we had this type DSL, this also opens up the door to not use the builtin Pyton types
(also allowing us to override things like `__init__` more easily...) In that case we would
have something like this:

```python
@expression
class A:
    def __init__(self, a: int, b: str) -> A:
        ...
```

Which calling it would not give you a real instance of `A` but instead an instance of
`Expression`? Which has the right dunder methods to look like it has all the same methods...

Then each method could simply be represented entirely in the DSL, not as builtin Python
methods... Making a bit "cleaner"...

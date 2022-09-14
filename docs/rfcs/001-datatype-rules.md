# RFC 0001 Datatype Rules

## Motivation
Currently in `metadsl` it is very cumbersome to define a datatype. A datatype is simply
a type that holds a collection of other types. For example, here is how we would define
a non generic pair of integers:

```python
class Pair(Expression):
    @expression
    @classmethod
    def create(cls, a: int, b: int) -> Pair:
        ...

    @expression
    @property
    def a(self) -> int:
        ...

    @expression
    @property
    def b(self) -> int:
        ...

    @expression
    def set_a(self, a: int) -> Pair:
        ...

    @expression
    def set_b(self, b: int) -> Pair:
        ...

@register
@rule
def pair_datatype_rule(a: int, b: int, a2: int, b2: int):
    yield Pair.create(a, b).a, a
    yield Pair.create(a, b).b, b
    yield Pair.create(a, b).set_a(a2), Pair.create(a2, b)
    yield Pair.create(a, b).set_b(b2), Pair.create(a, b2)
```

This not only is error prone, but it is also very verbose. These datatypes are used
often for things like holding state in an interpreter. The equivalent in pure Python
is the `@dataclass` decorator.

## Proposal

We propse adding two features to make this more succinct:

1. A `datatype_rule` function which will generate the rule for you based on inspecting
   the class.
2. Allow decorating all methods in a class automaticall in `@expression` by providing
   a `@wrap_methods` decorator.

With these two additions, the above example becomes:

```python
class Pair(Expression, wrap_methods=True):
    @classmethod
    def create(cls, a: int, b: int) -> Pair:
        ...

    @property
    def a(self) -> int:
        ...

    @property
    def b(self) -> int:
        ...

    def set_a(self, a: int) -> Pair:
        ...

    def set_b(self, b: int) -> Pair:
        ...

register(datatype_rule(Pair))
```

This is close to the minimal amount of code neccesary, to provide the proper method
definitions statically for MyPy to reason about. For example, we could autogenerate
these methods at runtime, but then statically a type checker would not be able to analyze
this code.

## Alternatives

### Support `@dataclass` directly

One obvious alternative is to support the `@dataclass` decorator directly. This would
end up with code something like this:

```python
@expression
@dataclass(frozen=True)
class Pair:
    a: int
    b: int

    def set_a(self, a: int) -> Pair:
        ...

    def set_b(self, b: int) -> Pair:
        ...

register(datatype_rule(Pair))
```

We would still need the functional setters, since we do not support mutations currently
(`p.a = 10` would not work).

We would also need to support the `__init__` method, which is not supported, we
use that for creating the actual expressions.

We would also need to turn the attributes into properties, so that we have  a method
to refer to on the class object...


Overall it also conflicts with our use of dataclasses as the actual expressions themselves.

If we were to go down this route, we might want to change some assumptions about our
base implementation. Instead actually having expression be instances of the type
itself, we could have them all be instances of `Expression` and have a seperate
`type` attribute, where we store our representation of the type.

This would in turn open up the library to support other types besides those supported here
in a more robust way... By in some sense proxying by default. It would mean we would
be asked to suport more of Python's type system (unions, inheritence..) but we wouldn't
have to do it all at once.

Then we have a differnce between a wrapped object and an unwrapped one. 

Anyways, the point being this too intensive to do right now. Let's postpone that.
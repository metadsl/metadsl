from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .pair import *
from .strategies import *

__all__ = ["Maybe", "collapse_maybe"]
T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")


class Maybe(Expression, typing.Generic[T], wrap_methods=True):
    """
    An optional value.
    """

    @classmethod
    def nothing(cls) -> Maybe[T]:
        ...

    @classmethod
    def just(cls, value: T) -> Maybe[T]:
        ...

    def match(self, nothing: U, just: Abstraction[T, U]) -> U:
        ...

    def default(self, value: T) -> T:
        return self.match(value, Abstraction[T, T].from_fn(lambda i: i))

    def __or__(self, other: Maybe[T]) -> Maybe[T]:
        """
        Like the <|> function https://en.wikibooks.org/wiki/Haskell/Alternative_and_MonadPlus
        """
        ...

    def __and__(self, other: Maybe[U]) -> Maybe[Pair[T, U]]:
        """
        >>> execute(Maybe[int].nothing() & Maybe.just("")) == Maybe[Pair[int, str]].nothing()
        True
        >>> execute(Maybe.just(10) & Maybe[str].nothing()) == Maybe[Pair[int, str]].nothing()
        True
        >>> execute(Maybe.just(10) & Maybe.just("")) == Maybe.just(Pair.create(10, ""))
        True
        """
        ...

    def map(self, just: Abstraction[T, U]) -> Maybe[U]:
        return self.match(
            Maybe[U].nothing(),
            Abstraction[U, Maybe[U]].from_fn(lambda v: Maybe.just(v)) + just,  # type: ignore
        )

    def flat_map(self, just: Abstraction[T, Maybe[U]]) -> Maybe[U]:
        return collapse_maybe(self.map(just))

    def expect(self) -> T:
        """
        If the maybe is something, it returns that value, if it is nothing,
        then it will never resolve.

        >>> execute(Maybe.just(10).expect())
        10
        >>> execute(Maybe.nothing().expect())
        Maybe.nothing().expect()
        """
        ...
    
    @classmethod
    def from_optional(cls, value: typing.Optional[T]) -> Maybe[T]:
        """
        >>> execute(Maybe[int].from_optional(None))
        Maybe[int].nothing()
        >>> execute(Maybe[int].from_optional(10))
        Maybe[int].just(10)
        """
        ...
        if value is None:
            return cls.nothing()
        else:
            return cls.just(value)

@register_core
@rule
def expect_maybe(x: T) -> R[T]:
    return Maybe.just(x).expect(), x


@expression
def collapse_maybe(x: Maybe[Maybe[T]]) -> Maybe[T]:
    return x.match(
        Maybe[T].nothing(), Abstraction[Maybe[T], Maybe[T]].from_fn(lambda m: m)
    )


register_core(default_rule(Maybe[T].map))
register_core(default_rule(Maybe[T].default))
register_core(default_rule(Maybe[T].flat_map))
register_core(default_rule(Maybe[T].from_optional))
register_core(default_rule(collapse_maybe))


@register_core  # type: ignore
@rule
def maybe_match(nothing: U, just: Abstraction[T, U], v: T) -> R[U]:
    yield Maybe[T].nothing().match(nothing, just), nothing
    yield Maybe.just(v).match(nothing, just), just(v)


@register_core
@rule
def maybe_or(x: T, v: Maybe[T]) -> R[Maybe[T]]:
    yield Maybe[T].nothing() | Maybe[T].nothing(), Maybe[T].nothing()
    yield Maybe.just(x) | v, Maybe.just(x)
    yield v | Maybe.just(x), Maybe.just(x)


@register_core
@rule
def maybe_and(left: Maybe[T], right: Maybe[U], left_v: T, right_v: U) -> R[Pair[T, U]]:
    yield Maybe[T].nothing() & right, Maybe[Pair[T, U]].nothing()
    yield left & Maybe[U].nothing(), Maybe[Pair[T, U]].nothing()
    yield Maybe.just(left_v) & Maybe.just(right_v), Maybe.just(
        Pair.create(left_v, right_v)
    )


@register_core
@rule
def push_down_maybe_maybe_match(
    m: Maybe[T],
    nothing: Maybe[U],
    just: Abstraction[T, Maybe[U]],
    nothing_outer: V,
    just_outer: Abstraction[U, V],
) -> R[V]:
    """
    If we have two matches, one after the other, push down the outer match inside the inner one.
    """
    return (
        m.match(nothing, just).match(nothing_outer, just_outer),
        lambda: m.match(
            nothing.match(nothing_outer, just_outer),
            Abstraction[T, V].from_fn(
                lambda t: just(t).match(nothing_outer, just_outer)
            ),
        ),
    )


@register_core
@rule
def match_identity(m: Maybe[T], var: T,) -> R[Maybe[T]]:
    """
    If we have a match that has each branch just create the same maybe, then remove the match.
    """
    return (m.match(Maybe[T].nothing(), Abstraction.create(var, Maybe.just(var))), m)

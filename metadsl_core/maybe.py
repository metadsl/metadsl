from __future__ import annotations
import typing

from metadsl import *
from .abstraction import *
from .rules import *
from .pair import *

__all__ = ["Maybe"]
T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Maybe(Expression, typing.Generic[T]):
    """
    An optional value.
    """

    @expression
    @classmethod
    def nothing(cls) -> Maybe[T]:
        ...

    @expression
    @classmethod
    def just(cls, value: T) -> Maybe[T]:
        ...

    @expression
    def match(self, nothing: U, just: Abstraction[T, U]) -> U:
        ...

    @expression
    def __or__(self, other: Maybe[T]) -> Maybe[T]:
        """
        Like the <|> function https://en.wikibooks.org/wiki/Haskell/Alternative_and_MonadPlus
        """
        ...

    @expression
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

    @expression
    def map(self, just: Abstraction[T, U]) -> Maybe[U]:
        return self.match(
            Maybe[U].nothing(),
            Abstraction.from_fn(Maybe[U].just) + just,  # type: ignore
        )


register(default_rule(Maybe[T].map))


@register  # type: ignore
@rule
def maybe_match(nothing: U, just: Abstraction[T, U], v: T) -> R[U]:
    yield Maybe[T].nothing().match(nothing, just), nothing
    yield Maybe.just(v).match(nothing, just), just(v)


@register
@rule
def maybe_or(x: T, v: Maybe[T]) -> R[Maybe[T]]:
    yield Maybe[T].nothing() | Maybe[T].nothing(), Maybe[T].nothing()
    yield Maybe.just(x) | v, Maybe.just(x)
    yield v | Maybe.just(x), Maybe.just(x)


@register
@rule
def maybe_and(left: Maybe[T], right: Maybe[U], left_v: T, right_v: U) -> R[Pair[T, U]]:
    yield Maybe[T].nothing() & right, Maybe[Pair[T, U]].nothing()
    yield left & Maybe[U].nothing(), Maybe[Pair[T, U]].nothing()
    yield Maybe.just(left_v) & Maybe.just(right_v), Maybe.just(
        Pair.create(left_v, right_v)
    )

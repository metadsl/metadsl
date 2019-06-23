from __future__ import annotations
import typing

from metadsl import *
from .abstraction import *
from .rules import *

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
    def map(self, just: Abstraction[T, U]) -> Maybe[U]:
        return self.match(
            Maybe[U].nothing(),
            just + Abstraction.from_fn(Maybe[U].just),  # type: ignore
        )


register(default_rule(Maybe.map))


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

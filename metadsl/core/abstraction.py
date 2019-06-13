from __future__ import annotations

from ..expressions import *
import typing

__all__ = ["Abstraction", "a"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Abstraction(Expression, typing.Generic[T, U]):
    @expression
    def __call__(self, arg: T) -> U:
        ...


def a(fn: typing.Callable[[T], U]) -> Abstraction[T, U]:
    raise NotImplementedError

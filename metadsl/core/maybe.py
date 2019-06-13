from __future__ import annotations
import typing

from ..expressions import *
from ..matching import *

__all__ = ["Maybe"]
T = typing.TypeVar("T")


class Maybe(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def just(cls, value: T) -> Maybe[T]:
        ...

    @expression
    @classmethod
    def nothing(cls) -> Maybe[T]:
        ...

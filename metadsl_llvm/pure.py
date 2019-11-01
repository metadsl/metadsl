from __future__ import annotations

import typing

__all__ = [
    # "Module",
    # "RegisteredFunctionOne",
    # "RegisteredFunctionTwo",
    # "RegisteredFunctionThree",
]
from metadsl import *
from metadsl_core import *

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


class Module(Expression):
    @expression
    @classmethod
    def create(cls, name: str) -> Module:
        ...

    @expression
    def register_function_one(
        self, fn: FunctionOne[T, U]
    ) -> Pair[Module, RegisteredFunctionOne[T, U]]:
        ...

    @expression
    def register_function_two(
        self, fn: FunctionTwo[T, U, V]
    ) -> Pair[Module, RegisteredFunctionTwo[T, U, V]]:
        ...

    @expression
    def register_function_three(
        self, fn: FunctionThree[T, U, V, X]
    ) -> Pair[Module, RegisteredFunctionThree[T, U, V, X]]:
        ...


class RegisteredFunctionOne(Expression, typing.Generic[T, U]):
    @expression
    def __call__(self, a: T) -> U:
        ...

    @expression
    def to_fn(self) -> typing.Callable[[T], U]:
        ...


class RegisteredFunctionTwo(Expression, typing.Generic[T, U, V]):
    @expression
    def __call__(self, a: T, b: U) -> V:
        ...

    @expression
    def to_fn(self) -> typing.Callable[[T, U], V]:
        ...


class RegisteredFunctionThree(Expression, typing.Generic[T, U, V, X]):
    @expression
    def __call__(self, a: T, b: U, c: V) -> X:
        ...

    @expression
    def to_fn(self) -> typing.Callable[[T, U, V], X]:
        ...

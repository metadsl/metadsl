from __future__ import annotations
import numbers

from metadsl import *
import typing

__all__ = ["Integer", "Tuple", "Number", "Optional", "Union"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Boolean(Expression):
    @staticmethod
    @expression
    def from_bool(b: E[bool]) -> Boolean:
        ...


class Integer(Expression):
    @staticmethod
    @expression
    def from_int(i: E[int]) -> Integer:
        ...

    @expression
    def __add__(self, other: Integer) -> Integer:
        ...

    @expression
    def __mul__(self, other: Integer) -> Integer:
        ...


class Tuple(Expression, typing.Generic[T]):
    """
    Mirrors the Python Tuple API, of a homogenous type.
    """

    @expression
    def __getitem__(self, index: Integer) -> T:
        ...

    @classmethod
    @expression
    def from_items(cls, *items: T) -> Tuple[T]:
        ...

    @expression
    def rest(self) -> Tuple[T]:
        ...


class Number(Expression):
    """
    Floating point, integer, or complex number.
    """

    @staticmethod
    @expression
    def from_number(i: numbers.Number) -> Number:
        ...

    @expression
    def __add__(self, other: Number) -> Number:
        ...

    @expression
    def __mul__(self, other: Number) -> Number:
        ...


class Optional(Expression, typing.Generic[T]):
    @staticmethod
    @expression
    def some(cls, value: T) -> Optional[T]:
        ...

    @classmethod
    @expression
    def none(cls) -> Optional[T]:
        ...


class Union(Expression, typing.Generic[T, U]):
    @classmethod
    @expression
    def left(cls, left: T) -> Union[T, U]:
        ...

    @staticmethod
    @expression
    def right(cls, right: U) -> Union[T, U]:
        ...

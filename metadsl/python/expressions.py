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

    @staticmethod
    def from_items(item_type: typing.Type[T], *items: T) -> Tuple[T]:
        # Can't use regular call b/c https://github.com/python/typing/issues/629
        return Tuple[item_type](Tuple.from_items, items)  # type: ignore

    @classmethod
    def from_items_expr(cls: typing.Type[Tuple[T]], *items: T) -> Tuple[T]:
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
    def some(value: T) -> Optional[T]:
        ...

    @staticmethod
    def none(t: typing.Type[T]) -> Optional[T]:
        return Optional[t](Optional.none_expr, ())  # type: ignore

    @classmethod
    def none_expr(cls: typing.Type[Optional[T]]) -> Optional[T]:
        ...


class Union(Expression, typing.Generic[T, U]):
    @staticmethod
    def left(left_t: typing.Type[T], right_t: typing.Type[U], left: T) -> Union[T, U]:
        return Union[left_t, right_t](Union.left_expr, (left,))  # type: ignore

    @staticmethod
    def right(left_t: typing.Type[T], right_t: typing.Type[U], right: U) -> Union[T, U]:
        return Union[left_t, right_t](Union.right_expr, (right,))  # type: ignore

    @classmethod
    def left_expr(cls: typing.Type[Union[T, U]], left: T) -> Union[T, U]:
        ...

    @classmethod
    def right_expr(cls: typing.Type[Union[T, U]], right: U) -> Union[T, U]:
        ...

# from __future__ import annotations
# import numbers

# from metadsl import *
# import typing

# __all__ = ["Integer", "Tuple", "Number", "Optional", "Union"]

# T = typing.TypeVar("T")
# U = typing.TypeVar("U")


# class Boolean(Expression):
#     @staticmethod
#     @expression
#     def from_bool(b: bool) -> Boolean:
#         ...


# class Integer(Expression):
#     @staticmethod
#     @expression
#     def from_int(i: int) -> Integer:
#         ...

#     @expression
#     def __add__(self, other: Integer) -> Integer:
#         ...

#     @expression
#     def __mul__(self, other: Integer) -> Integer:
#         ...


# class Tuple(Expression, typing.Generic[T]):
#     """
#     Mirrors the Python Tuple API, of a homogenous type.
#     """

#     @expression
#     def __getitem__(self, index: Integer) -> T:
#         ...

#     @classmethod
#     @expression
#     def from_items(cls, *items: T) -> Tuple[T]:
#         ...

#     @expression
#     def rest(self) -> Tuple[T]:
#         ...


# class Number(Expression):
#     """
#     Floating point, integer, or complex number.
#     """

#     @staticmethod
#     @expression
#     def from_number(i: numbers.Number) -> Number:
#         ...

#     @expression
#     def __add__(self, other: Number) -> Number:
#         ...

#     @expression
#     def __mul__(self, other: Number) -> Number:
#         ...


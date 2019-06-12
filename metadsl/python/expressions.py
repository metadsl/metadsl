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
    def from_bool(b: bool) -> Boolean:
        ...


class Integer(Expression):
    @staticmethod
    @expression
    def from_int(i: int) -> Integer:
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


# class Convert(Expression, typing.Generic[T]):
#     @expression
#     @classmethod
#     def convert(cls, value: object) -> T:
#         ...


# class Optional(Expression, typing.Generic[T]):
#     @expression
#     @classmethod
#     def some(cls, value: T) -> Optional[T]:
#         ...

#     @expression
#     @classmethod
#     def none(cls) -> Optional[T]:
#         ...


# @rule
# def convert_optional_none() -> R[Optional[T]]:
#     """
#     When the value is an instance of the type being converted, we can convert it.
#     """
#     return Convert[Optional[T]].convert(None), lambda: Optional[T].none()


# class Abstraction(Expression, typing.Generic[T, U]):
#     @expression
#     def __call__(self, v: T) -> U:
#         ...


# def abstraction(fn: typing.Callable[[T], U]) -> Abstraction[T, U]:
#     ...


# V = typing.TypeVar("V")


# class Optional(Expression, typing.Generic[T]):
#     pass

#     @expression
#     def match(self, none: U, some: Abstraction[T, U]) -> U:
#         ...

#     @expression
#     def map(self, fn: Abstraction[T, V]) -> Optional[V]:
#         return self.match(none(V), abstraction(lambda v: some(fn(v))))


# @expression
# def optional_either(
#     l: Optional[T], r: Optional[U], l_fn: Abstraction[T, V], r_fn: Abstraction[U, V]
# ) -> Optional[V]:
#     ...


# @expression
# def some(value: T) -> Optional[T]:
#     ...


# @expression
# def none(tp: typing.Type[T]) -> Optional[T]:
#     ...


# @expression
# def convert(type: typing.Type[T], value: object) -> Optional[T]:
#     """
#     Converts a value to a certain type or none if it cannot.
#     """
#     ...


# @rule
# def convert_optional(x: object) -> R[Optional[Optional[T]]]:
#     return (
#         convert(Optional[T], x),
#         lambda: some(none(T) if x is None else convert(T, x)),
#     )


# assert convert_optional(convert(Optional[int], None)) == some(none(int))
# assert convert_optional(convert(Optional[int], 123)) == some(some(convert(int, 123)))


# class Union(Expression, typing.Generic[T, U]):
#     pass


# @expression
# def left(left: T, right_type: typing.Type[U]) -> Union[T, U]:
#     ...


# @expression
# def right(left_type: typing.Type[T], right: U) -> Union[T, U]:
#     ...


# @rule
# def convert_union(x: object) -> R[Optional[Union[T, U]]]:
#     return (
#         convert(Union[T, U], x),
#         lambda: optional_either(
#             convert(T, x),
#             convert(U, x),
#             abstraction(lambda l: left(l, U)),
#             abstraction(lambda r: left(r, T)),
#         ),
#     )


class Optional(Expression, typing.Generic[T]):
    @classmethod
    @expression
    def some(cls, value: T) -> Optional[T]:
        ...

    @classmethod
    @expression
    def none(cls) -> Optional[T]:
        ...


class Converter(Expression, typing.Generic[T]):
    @classmethod
    @expression
    def convert(cls, value: object) -> Optional[T]:
        """
        Converts a value to type T or none if it cannot.
        """
        ...


@rule
def convert_optional(x: object) -> R[Optional[Optional[T]]]:
    return (
        Converter[Optional[T]].convert(x),
        lambda: Optional.some(
            Optional[T].none() if x is None else Converter[T].convert(x)
        ),
    )


assert convert_optional(Converter[int].convert(None)) == Optional.some(
    Optional[int].none()
)
assert convert_optional(Converter[int].convert(123)) == Optional.some(
    Converter[int].convert(123)
)

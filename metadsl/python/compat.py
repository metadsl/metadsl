from __future__ import annotations

import numbers
import typing

import metadsl.python.pure as py_pure
import typing_inspect
from metadsl import *
from metadsl.typing_tools import safe_issubclass

__all__ = ["Integer", "Number", "Number", "IntegerTuple"]

T = typing.TypeVar("T")


@register_converter
def _bool_to_boolean(t: typing.Type[T], value: object) -> T:
    if safe_issubclass(t, py_pure.Boolean) and isinstance(value, bool):
        return typing.cast(T, py_pure.Boolean.from_bool(value))
    return NotImplemented


class Integer(Wrap[py_pure.Integer]):
    @wrap(py_pure.Integer.__add__)
    def __add__(self, other: object) -> Integer:
        ...

    @wrap(py_pure.Integer.__mul__)
    def __mul__(self, other: object) -> Integer:
        ...


@register_converter
def _int_to_integer(t: typing.Type[T], value: object) -> T:
    if (
        safe_issubclass(t, py_pure.Integer)
        and isinstance(value, int)
        and not isinstance(value, bool)
    ):
        return typing.cast(T, py_pure.Integer.from_int(value))
    return NotImplemented


class Number(Wrap[py_pure.Number]):
    @wrap(py_pure.Number.__add__)
    def __add__(self, other: object) -> Number:
        ...

    @wrap(py_pure.Number.__mul__)
    def __mul__(self, other: object) -> Number:
        ...


@register_converter
def _number_to_number(t: typing.Type[T], value: object) -> T:
    if safe_issubclass(t, py_pure.Number) and isinstance(value, numbers.Number):
        return typing.cast(T, py_pure.Number.from_number(value))
    return NotImplemented


class IntegerTuple(Wrap[py_pure.Tuple[py_pure.Integer]]):
    @wrap(py_pure.Tuple.__getitem__)
    def __getitem__(self, index: object) -> Integer:
        ...


@register_converter
def _tuple_to_tuple(t: typing.Type[T], value: object) -> T:
    if safe_issubclass(t, py_pure.Tuple) and isinstance(value, tuple):
        inner_type, = typing_inspect.get_args(t)
        return typing.cast(
            T,
            py_pure.Tuple.from_items(
                inner_type, *(convert(inner_type, a) for a in value)
            ),
        )
    return NotImplemented


@register_converter
def _to_optional(t: typing.Type[T], value: object) -> T:
    if safe_issubclass(t, py_pure.Optional):
        inner_type, = typing_inspect.get_args(t)
        if value is None:
            return typing.cast(T, py_pure.Optional.none(inner_type))
        return typing.cast(T, py_pure.Optional.some(convert(inner_type, value)))
    return NotImplemented


@register_converter
def _to_union(t: typing.Type[T], value: object) -> T:
    if safe_issubclass(t, py_pure.Union):
        left_type, right_type = typing_inspect.get_args(t)

        try:
            left_converted = convert(left_type, value)
        except NotImplementedError:
            left_converted = None

        try:
            right_converted = convert(right_type, value)
        except NotImplementedError:
            right_converted = None
        if left_converted is not None and right_converted is not None:
            raise ValueError(f"Ambigious conversion: {value} to {t}")

        if left_converted is None and right_converted is None:
            return NotImplemented
        if left_converted:
            return typing.cast(
                T, py_pure.Union.left(left_type, right_type, left_converted)
            )
        return typing.cast(
            T, py_pure.Union.right(left_type, right_type, right_converted)
        )
    return NotImplemented

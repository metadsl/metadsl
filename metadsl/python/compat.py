from metadsl.expressions import *
import typing
import numbers
import dataclasses

import metadsl.python.pure as py_pure

__all__ = ["Integer", "TupleOfIntegers", "Number", "Optional", "Boolean"]

T = typing.TypeVar("T", bound=Instance)


class Boolean(Instance):
    """
    bool
    """

    @classmethod
    def from_value(cls, value: typing.Any) -> "Boolean":
        if isinstance(value, Boolean):
            return value
        if isinstance(value, py_pure.Boolean):
            return cls.from_pure(value)
        if isinstance(value, bool):
            return cls(value)
        raise TypeError(value)

    @classmethod
    def from_pure(cls, p: py_pure.Boolean) -> "Boolean":
        return cls(p.__value__)

    @property
    def pure(self) -> py_pure.Boolean:
        return py_pure.Boolean(self.__value__)


class Integer(Instance):
    """
    int
    """

    @classmethod
    def from_value(cls, value: typing.Any) -> "Integer":
        if isinstance(value, Integer):
            return value
        if isinstance(value, py_pure.Integer):
            return cls.from_pure(value)
        if isinstance(value, int):
            return cls(value)
        raise TypeError(value)

    @classmethod
    def from_pure(cls, p: py_pure.Integer) -> "Integer":
        return cls(p.__value__)

    @property
    def pure(self) -> py_pure.Integer:
        return py_pure.Integer(self.__value__)


class Number(Instance):
    """
    numbers.Number
    """

    @classmethod
    def from_value(cls, value: typing.Any) -> "Number":
        if isinstance(value, Number):
            return value
        if isinstance(value, py_pure.Number):
            return cls.from_pure(value)
        if isinstance(value, numbers.Number):
            return cls(value)
        raise TypeError(value)

    @classmethod
    def from_pure(cls, p: py_pure.Number) -> "Number":
        return cls(p.__value__)

    @property
    def pure(self) -> py_pure.Number:
        return py_pure.Number(self.__value__)


class TupleOfIntegers(Instance):
    """
    typing.Tuple[int]
    """

    @classmethod
    def from_pure(cls, p: py_pure.TupleOfIntegers) -> "TupleOfIntegers":
        return cls(p.__value__)

    @property
    def pure(self) -> py_pure.TupleOfIntegers:
        return py_pure.TupleOfIntegers(self.__value__)

    def __getitem__(self, index: typing.Any) -> Integer:
        return Integer.from_pure(self.pure[Integer.from_value(index).pure])

    @classmethod
    def create(cls, *values: typing.Any) -> "TupleOfIntegers":
        return cls.from_pure(
            py_pure.TupleOfIntegers.create(
                *(Integer.from_value(value).pure for value in values)
            )
        )

    @classmethod
    def from_value(cls, value: typing.Any) -> "TupleOfIntegers":
        if isinstance(value, TupleOfIntegers):
            return value
        if isinstance(value, py_pure.TupleOfIntegers):
            return cls.from_pure(value)
        if isinstance(value, tuple):
            return cls(value)
        raise TypeError(value)


@dataclasses.dataclass(frozen=True)
class Optional(Instance, typing.Generic[T]):
    inner_type: InstanceType[T]

    @classmethod
    def from_pure(cls, p: py_pure.Optional[T]) -> "Optional[T]":
        return cls(p.__value__, p.inner_type)

    @property
    def pure(self) -> py_pure.Optional[T]:
        return py_pure.Optional(self.__value__, self.inner_type)

    @classmethod
    def from_value(
        cls, inner_type: InstanceType[T], value: typing.Any
    ) -> "Optional[T]":
        if value is None:
            return Optional(Call(py_pure.Optional.create_none_call, ()), inner_type)
        # TODO: Add casting from existing types
        return cls.from_pure(py_pure.Optional.create_some(inner_type(value)))

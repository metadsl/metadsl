from __future__ import annotations

from metadsl import *
import typing
import dataclasses

import metadsl.python.pure as py_pure

__all__ = ["Integer", "Tuple", "Number", "Optional", "Boolean", "create_instance"]

T = typing.TypeVar("T")


def create_instance(instance_type: InstanceType[T], value: object) -> T:
    """
    Takes an instance type and a Python value and creates an instance of that type.
    """
    # TODO: Make this dispatch extensible

    # Instances should be passed through, changing the type
    if isinstance(value, Instance):
        return instance_type(value.__value__)  # type: ignore

    # Tuples
    if instance_type.type == py_pure.Tuple and isinstance(value, tuple):
        item_type, = instance_type.args
        items = [create_instance(item_type, item) for item in value]
        return py_pure.Tuple.from_items(item_type, *items)  # type: ignore

    # Optional
    if instance_type.type == py_pure.Optional:
        inner_type, = instance_type.args
        if value is None:
            return py_pure.Optional.create_none(inner_type)  # type: ignore
        return py_pure.Optional.create_some(  # type: ignore
            create_instance(inner_type, value)
        )
    if isinstance(value, dict):
        value = tuple(value.items())

    return instance_type(value)

class Boolean(Instance):
    """
    bool
    """

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
    def from_pure(cls, p: py_pure.Number) -> "Number":
        return cls(p.__value__)

    @property
    def pure(self) -> py_pure.Number:
        return py_pure.Number(self.__value__)


@dataclasses.dataclass(frozen=True)
class Tuple(Instance, typing.Generic[T]):
    item_type: InstanceType[T]

    @classmethod
    def from_pure(cls, p: py_pure.Tuple[typing.Any], item_type: InstanceType[T]) -> "Tuple[T]":
        return cls(p.__value__, item_type)

    @property
    def pure(self) -> py_pure.Tuple[T]:
        return py_pure.Tuple(self.__value__, self.item_type)

    def __getitem__(self, index: typing.Any) -> T:
        return self.pure[create_instance(instance_type(Integer), index).pure]


@dataclasses.dataclass(frozen=True)
class Optional(Instance, typing.Generic[T]):
    inner_type: InstanceType[T]

    @classmethod
    def from_pure(cls, p: py_pure.Optional[T]) -> "Optional[T]":
        return cls(p.__value__, p.inner_type)

    @property
    def pure(self) -> py_pure.Optional[T]:
        return py_pure.Optional(self.__value__, self.inner_type)

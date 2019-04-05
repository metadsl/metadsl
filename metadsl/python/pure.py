from metadsl.expressions import *
import typing
import dataclasses

__all__ = [
    "Boolean",
    "Integer",
    "Tuple",
    "Number",
    "Optional",
    "Abstraction",
    "Instance",
]

T = typing.TypeVar("T", bound=Instance)
U = typing.TypeVar("U", bound=Instance)


class Boolean(Instance):
    pass


class Integer(Instance):
    pass


@dataclasses.dataclass(frozen=True)
class Tuple(Instance, typing.Generic[T]):
    """
    Mirrors the Python Tuple API, of a homogenous type.
    """

    item_type: InstanceType[T]

    @call(lambda self, index: self.args[0])
    def __getitem__(self, index: Integer) -> T:
        ...

    @staticmethod
    def from_items(item_type: InstanceType[T], *items: T) -> "Tuple[T]":
        return call(lambda *items: item_type)(Tuple.from_items_call)(*items)

    @staticmethod
    def from_items_call(*items: T) -> "Tuple[T]":
        ...


class Number(Instance):
    """
    Floating point, integer, or complex number.
    """

    pass


@dataclasses.dataclass(frozen=True)
class Abstraction(Instance, typing.Generic[T, U]):
    return_type: InstanceType[U]

    @call(lambda self, arg: self.return_type)
    def __call__(self, arg: T) -> U:
        ...


@dataclasses.dataclass(frozen=True)
class Optional(Instance, typing.Generic[T]):
    inner_type: InstanceType[T]

    @call(lambda self, none, some: none)
    def match(self, none: U, some: Abstraction[T, U]) -> U:
        ...

    @staticmethod
    @call(lambda value: instance_type(Optional, value))
    def create_some(value: T) -> "Optional[T]":
        ...

    @classmethod
    def create_none(cls, inner_type: InstanceType[T]) -> "Optional[T]":
        return call(lambda: instance_type(Optional, inner_type))(cls.create_none_call)()

    @classmethod
    def create_none_call(cls):
        ...

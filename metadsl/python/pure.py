from metadsl.expressions import *
import typing
import dataclasses

__all__ = [
    "Boolean",
    "Integer",
    "TupleOfIntegers",
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


class TupleOfIntegers(Instance):
    @call(lambda self, index: instance_type(Integer))
    def __getitem__(self, index: Integer) -> Integer:
        ...

    @call(lambda *values: instance_type(TupleOfIntegers))
    @staticmethod
    def create(*values: Integer) -> "TupleOfIntegers":
        ...


class Number(Instance):
    """
    Floating point, integer, or complex number.
    """

    pass


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


# class Boolean(Instance):
#     @call(lambda self, true, false: true)
#     def if_(self, true: T, false: Abstraction[T, U]) -> U:
#         ...

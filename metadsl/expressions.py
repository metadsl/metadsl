import dataclasses
import typing

# import functools
# import typing_extensions
# from .functools import memoize, unsafe_hash
from .calls import *

__all__ = [
    "RecursiveCall",
    "to_expression",
    "from_expression",
    "ValueType",
    "ExpressionType",
    "ExpressionFolder",
    "expression_replacer",
]


ArgType = typing.TypeVar("ArgType")
ReturnType = typing.TypeVar("ReturnType")
NewArgType = typing.TypeVar("NewArgType")


@dataclasses.dataclass
class RecursiveCall(typing.Generic[ArgType, ReturnType]):
    function: typing.Callable[..., ReturnType]
    args: typing.Tuple[ArgType, ...]
    # __unsafe_hash__: int = dataclasses.field(init=False)

    def __str__(self):
        return f"{self.function.__name__}({', '.join(map(str, self.args))})"

    def __repr__(self):
        return f"RecursiveCall({self.function.__name__}, {self.args})"

    # def __post_init__(self):
    #     self.__unsafe_hash__ = hash(
    #         (self.function,) + tuple(map(unsafe_hash, self.args))
    #     )


T = typing.TypeVar("T")


@dataclasses.dataclass
class ExpressionFolder(typing.Generic[T]):
    """
    Traverses this expression graph and transforms each node, from the bottom up.

    You provide two functions, one to transform the leaves, and a second to transform the calls.

    Each node is transformed once, and only once, based on it's id.
    """

    value_fn: typing.Callable[[object], T]
    call_fn: typing.Callable[[typing.Callable, typing.Tuple[T, ...]], T]

    def __call__(self, expr: object):
        if isinstance(expr, RecursiveCall):
            return self.call_fn(  # type: ignore
                expr.function, tuple(self(arg) for arg in expr.args)
            )
        return self.value_fn(expr)  # type: ignore


ValueType = typing.Union[T, Call[typing.Any, T]]
ExpressionType = typing.Union[T, RecursiveCall[typing.Any, T]]


def to_expression(val: ValueType[T]) -> ExpressionType[T]:
    if isinstance(val, Instance):
        return to_expression(val._call)
    if isinstance(val, Call):
        return RecursiveCall(
            val.function, tuple(to_expression(arg) for arg in val.args)
        )
    return val


_from_expression_folder = ExpressionFolder(lambda v: v, lambda fn, args: fn(*args))


def from_expression(val: ExpressionType[T]) -> T:
    return _from_expression_folder(val)


@dataclasses.dataclass
class ExpressionReplacer:
    # Not using dict, because we might not have hashable keys
    mapping: typing.Tuple[typing.Tuple[typing.Any, typing.Any], ...]
    folder: ExpressionFolder = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self._value_fn, self._call_fn)

    def __call__(self, expr):
        return self.folder(expr)

    def _value_fn(self, o):
        return self._get(o, o)

    def _call_fn(self, fn, args):
        call = RecursiveCall(fn, args)
        return self._get(call, call)

    def _get(self, key, default):
        for actual_key, value in self.mapping:
            if actual_key == key:
                return value
        return default


def expression_replacer(
    mapping: typing.Tuple[typing.Tuple[typing.Any, typing.Any], ...]
) -> typing.Callable:
    return ExpressionReplacer(mapping)

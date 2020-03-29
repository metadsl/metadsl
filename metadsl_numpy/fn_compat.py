from __future__ import annotations
import typing
import types
import inspect

from metadsl import *
from metadsl_core import *

from .injest import *

__all__: typing.List[str] = []


T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


FUNCTION_TYPE = typing.Union[
    typing.Type[FunctionZero],
    typing.Type[FunctionOne],
    typing.Type[FunctionTwo],
    typing.Type[FunctionThree],
]
FUNCTIONS: typing.List[FUNCTION_TYPE] = [
    FunctionZero,
    FunctionOne,
    FunctionTwo,
    FunctionThree,
]


# @guess_type.register
# def guess_fn(fn: types.FunctionType) -> FUNCTION_TYPE:
#     n_args = 0
#     for param in inspect.signature(fn).parameters.values():
#         if param.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD:
#             raise NotImplementedError(
#                 f"Don't know how to infer function type for {fn} because it has non positional args "
#             )
#         n_args += 1
#     try:
#         return FUNCTIONS[n_args]
#     except IndexError:
#         raise NotImplementedError(
#             f"No function type yet for a function with {n_args} args."
#         )


# @register_convert
# @rule
# def convert_fn_zero(fn: typing.Callable[[], T]) -> R[Maybe[FunctionZero[T]]]:
#     return (
#         Converter[FunctionZero[T]].convert(fn),
#         Maybe.just(FunctionZero.from_fn(fn)),
#     )

# @register_convert
# @rule
# def convert_fn_one(fn: typing.Callable[[T], U]) -> R[Maybe[FunctionZero[T, U]]]:
#     return (
#         Converter[FunctionZero].convert(fn),
#         Maybe.just(FunctionZero.from_fn(fn)),
#     )

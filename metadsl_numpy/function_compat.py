from __future__ import annotations
import typing
import types
import functools
import typing_inspect

from metadsl import *
from metadsl_core import *
from metadsl.typing_tools import ToCallable, get_type
from metadsl_rewrite import *

from .injest import *
from .boxing import *

__all__: typing.List[str] = []

T = typing.TypeVar("T")
U = typing.TypeVar("U")

V = typing.TypeVar("V")
X = typing.TypeVar("X")


# class FunctionZeroCompat(Expression, typing.Generic[T, U]):
#     @expression
#     @classmethod
#     def from_maybe_function(
#         cls, fn: Maybe[FunctionZero[Maybe[U]]]
#     ) -> FunctionOneCompat[T, U]:
#         ...

#     @expression
#     @classmethod
#     def from_function(cls, fn: FunctionZero[T]) -> FunctionOneCompat[T, U]:
#         ...

#     @expression
#     def __call__(self, arg: object) -> T:
#         ...


class FunctionOneCompat(Expression, typing.Generic[T]):
    """
    Compat function with inner function mapping from U -> Maybe[V]

    that converts any arg to U and then boxes the result into the compat type T.
    """

    @expression
    @classmethod
    def box(cls, fn: Maybe[FunctionOne[U, Maybe[V]]]) -> FunctionOne[object, T]:
        ...


@register_convert
@rule
def box_function_one(v: Maybe[FunctionOne[U, Maybe[V]]]) -> R[FunctionOne[object, T]]:
    return (
        Boxer[FunctionOne[object, T], FunctionOne[U, Maybe[V]]].box(v),
        FunctionOneCompat[T].box(v),
    )


@expression
def converter_name(name: str) -> str:
    return name + "_convert"


register_core(default_rule(converter_name))


@register_convert
@rule
def function_one_box_rule(fn: FunctionOne[U, Maybe[V]]) -> R[FunctionOne[object, T]]:

    return (
        FunctionOneCompat[T].box(Maybe.just(fn)),
        lambda: FunctionOne[object, T].from_fn(
            lambda o: Boxer[T, V].box(Converter[U].convert(o).flat_map(fn.abstraction)),
            name=Maybe.just(converter_name(fn.name)),
        ),
    )


# Register for anything that could be thought of as a callable, but don't use typing.Callable
# since then callable-ish things would be supported like  FunctionOne themselves
@guess_type.register(ToCallable)
def guess_python_function_tp(
    fn: typing.Callable,
) -> typing.Union[
    typing.Tuple[typing.Type[FunctionZero], typing.Type[FunctionZero]],
    typing.Tuple[typing.Type[FunctionOne], typing.Type[FunctionOne]],
]:
    """
    Guesses the type of a function. The args of the function should
    all be compat types.
    """
    arg_tps, return_tp = typing_inspect.get_args(get_type(fn))

    return_compat_tp, return_inner_tp = guess_type_of_type(return_tp)

    arg_inner_tps = [guess_type_of_type(arg_tp)[1] for arg_tp in arg_tps]
    n_args = len(arg_inner_tps)

    if n_args == 0:
        raise NotImplementedError
        # return (
        #     FunctionZeroCompat[return_compat_tp, return_inner_tp],
        #     FunctionZero[Maybe[return_inner_tp]],
        # )
    if n_args == 1:
        return (
            FunctionOne[object, return_compat_tp],  # type: ignore
            FunctionOne[arg_inner_tps[0], Maybe[return_inner_tp]],  # type: ignore
        )
    raise NotImplementedError


@guess_type.register
def guess_function_one_tp(fn: FunctionOne):
    arg_tp, ret_tp = typing_inspect.get_args(get_type(fn))
    ret_compat_tp, ret_inner_tp = guess_type_of_type(ret_tp)

    return FunctionOne[object, ret_compat_tp], FunctionOne[arg_tp, Maybe[ret_inner_tp]]  # type: ignore


# TODO:
# * Add box logic for maybe x, y to FunctionOne

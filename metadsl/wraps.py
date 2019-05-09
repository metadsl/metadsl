"""
You can wrap an exprssion type to provide all the same methods,
but do type conversion for the arguments.
"""

import typing
import functools

from .expressions import Expression
from .conversion import convert, register_converter
from .typing_tools import *
import dataclasses

__all__ = ["Wrap", "wrap"]
T = typing.TypeVar("T")
T_expression = typing.TypeVar("T_expression", bound=Expression)


@dataclasses.dataclass
class Wrap(typing.Generic[T_expression]):
    _expression: T_expression


@register_converter
def _unwrap(t: typing.Type[T], v: object) -> T:
    if isinstance(v, Wrap) and safe_isinstance(v._expression, t):
        return v._expression
    return NotImplemented


T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


def wrap(original_fn: typing.Callable) -> typing.Callable[[T_callable], T_callable]:
    def wrap_inner(fn: T_callable, original_fn=original_fn) -> T_callable:
        """
        Converts each of the arguments to type.
        """

        @functools.wraps(fn)
        def wrap_inner_inner(*args, fn=fn, original_fn=original_fn) -> Wrap:

            return_hint = typing.get_type_hints(fn)["return"]
            first_arg_could_be_self = args and isinstance(args[0], Wrap)

            arg_hints = get_arg_hints(
                original_fn.__wrapped__,
                get_type(args[0]._expression) if first_arg_could_be_self else None,
            )
            converted_args = (
                convert(hint, arg) if hint else arg
                for hint, arg in zip(arg_hints, args)
            )
            return return_hint(original_fn(*converted_args))

        return typing.cast(T_callable, wrap_inner_inner)

    return wrap_inner

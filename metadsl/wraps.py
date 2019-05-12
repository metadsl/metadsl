# """
# To create a version of an expression class that can
# deal with Pyhon values, you should subclass
# it and decorate each of the methods you want
# to wrap with `wrap_method`, supplying a new signature
# that takes in any python object and returns a wrapped
# expression.

# For a function, decorate it with `wrap`, passing in the
# original function first.
# """

# import typing
# import functools

# from .expressions import *
# from .conversion import *
# from .typing_tools import *

# __all__ = ["wrap", "wrap_method"]
# T = typing.TypeVar("T")


# T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


# def wrap_method(fn: T_callable) -> T_callable:
#     """
#     Wraps a method of an expression to call it's super method but first converting
#     all arguments to expressions.
#     """
#     return_hint = typing.get_type_hints(fn)["return"]

#     def wrap_method_inner(self, *args, fn=fn, _return_type=return_hint) -> Expression:
#         original_fn = getattr(super(type(self), self), fn.__name__)
#         arg_hints = get_arg_hints(original_fn.__wrapped__, self)
#         converted_args = (
#             convert(hint, arg) if hint else arg for hint, arg in zip(arg_hints, args)
#         )
#         return original_fn(*converted_args, _return_type=_return_type)

#     return typing.cast(T_callable, wrap_method_inner)


# def wrap(original_fn: typing.Callable) -> typing.Callable[[T_callable], T_callable]:
#     def wrap_inner(fn: T_callable, original_fn=original_fn) -> T_callable:
#         """
#         Converts each of the arguments to type.
#         """
#         return_hint = typing.get_type_hints(fn)["return"]
#         arg_hints = get_arg_hints(original_fn.__wrapped__)

#         @functools.wraps(fn)
#         def wrap_inner_inner(
#             *args,
#             original_fn=original_fn,
#             arg_hints=arg_hints,
#             _return_type=return_hint
#         ) -> Expression:
#             converted_args = (
#                 convert(hint, arg) if hint else arg
#                 for hint, arg in zip(arg_hints, args)
#             )
#             return original_fn(*converted_args, _return_type=_return_type)

#         return typing.cast(T_callable, wrap_inner_inner)

#     return wrap_inner

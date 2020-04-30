from __future__ import annotations

import dataclasses
import itertools
import typing

import typing_inspect

from .typing_tools import *

__all__ = [
    "Expression",
    "expression",
    "PlaceholderExpression",
    "IteratedPlaceholder",
    "create_iterated_placeholder",
    "clone_expression",
]

T = typing.TypeVar("T")
T_expression = typing.TypeVar("T_expression", bound="Expression")
CALLABLE = typing.TypeVar("CALLABLE", bound=typing.Callable)


@dataclasses.dataclass(eq=False, repr=False)
class Expression(GenericCheck):
    """
    Top level object.
    Subclass this type and provide relevent methods for your type. Do not add any fields.

    Properties:

    Calling the function, after replacing the typevars in it (if it is a bound method),
    with the args and kwargs should resualt in an equivalent expression:

    replace_fn_typevars(self.function, self.typevars)(*self.args, **self.kwargs) == self
    
    The return type of the function, inferred by replacing the typevars in and with these args and kwargs,
    should match the type of the expression. If the return type of the function is not subclass of expression,
    then this should be a PlaceholderExpression of that type.
    """

    function: typing.Callable
    args: typing.List[object]
    kwargs: typing.Dict[str, object]

    def __str__(self):
        arg_strings = (str(arg) for arg in self.args)
        kwarg_strings = (f"{str(k)}={str(v)}" for k, v in self.kwargs.items())
        return f"{self._function_str}({', '.join(itertools.chain(arg_strings, kwarg_strings))})"

    @property
    def _function_str(self):
        return getattr(self.function, "__qualname__", str(self.function))

    @property
    def _type_str(self):
        t = get_type(self)
        if isinstance(t, typing._GenericAlias):  # type: ignore
            return repr(t)
        return typing._type_repr(t)  # type: ignore

    def __repr__(self):
        return (
            f"{self._type_str}({self.function}, {repr(self.args)}, {repr(self.kwargs)})"
        )

    def _map(
        self: T_expression,
        fn: typing.Callable[[T], T],
        function_fn: typing.Callable[[CALLABLE], CALLABLE] = None,
        type_fn: typing.Callable[
            [typing.Type[T_expression]], typing.Type[T_expression]
        ] = None,
    ) -> T_expression:
        """
        Map a function on all args and recreate function.

        """
        new_type: typing.Type[T_expression] = typing_inspect.get_generic_type(self)

        new_expr = type(self)(
            function=function_fn(self.function) if function_fn else self.function,  # type: ignore
            args=[fn(typing.cast(T, arg)) for arg in self.args],
            kwargs={k: fn(typing.cast(T, v)) for k, v in self.kwargs.items()},
        )
        # copy generic class
        if hasattr(self, "__orig_class__"):
            new_expr.__orig_class__ = (  # type: ignore
                type_fn(self.__orig_class__) if type_fn else self.__orig_class__  # type: ignore
            )

        return new_expr

    def __eq__(self, value) -> bool:
        if not isinstance(value, Expression):
            return False

        return (
            self.function == value.function
            and self.args == value.args
            and self.kwargs == value.kwargs
        )


def clone_expression(expr: T) -> T:
    if isinstance(expr, Expression):
        return expr._map(clone_expression)  # type: ignore
    return expr


class PlaceholderExpression(Expression, OfType[T], typing.Generic[T]):
    """
    An expression that represents a type of `T`, for example T could be `int`.

    This is needed when a function returns a non expression type, it still has to return
    an expression under the covers until it has been replaced.

    It is also needed when using Wildcards in expressions when doing matching.
    """

    def __iter__(self):
        return iter((create_iterated_placeholder(self),))  # type: ignore


def extract_expression_type(t: typing.Type) -> typing.Type[Expression]:
    if issubclass(t, Expression):
        return t
    return PlaceholderExpression[t]  # type: ignore


T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


def wrapper(fn, args, kwargs, return_type):
    expr_return_type = extract_expression_type(return_type)
    # Clone expression when returning it, so if if we mutate child expression
    # those one won't be mutated
    return clone_expression(expr_return_type(fn, list(args), kwargs))


def expression(fn: T_callable) -> T_callable:
    """
    Creates an expresion object by wrapping a Python function and providing a function
    that will take in the args and return an expression of the right type.
    """

    return typing.cast(T_callable, infer(fn, wrapper))


class IteratedPlaceholder(Expression, ExpandedType, typing.Generic[T]):
    pass


@expression
def create_iterated_placeholder(
    i: PlaceholderExpression[typing.Sequence[T]],
) -> IteratedPlaceholder[T]:
    """
    If a placeholder is of an iterable T, calling iter on it should return an iterable placeholder of the inner type.

    Used in matching with variable args.
    """
    ...

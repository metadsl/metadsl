from __future__ import annotations

import dataclasses
import itertools
import typing

from .typing_tools import *

__all__ = [
    "Expression",
    "expression",
    "ExpressionFolder",
    "ExpressionReplacer",
    "PlaceholderExpression",
    "IteratedPlaceholder",
    "create_iterated_placeholder",
]

T_expression = typing.TypeVar("T_expression", bound="Expression")


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
        return str(t)

    def __repr__(self):
        return (
            f"{self._type_str}({self.function}, {repr(self.args)}, {repr(self.kwargs)})"
        )

    def __eq__(self, value) -> bool:
        if not isinstance(value, Expression):
            return False

        return (
            self.function == value.function
            and self.args == value.args
            and self.kwargs == value.kwargs
        )


T = typing.TypeVar("T")


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
    return expr_return_type(fn, list(args), kwargs)


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


T_Expression = typing.TypeVar("T_Expression", bound="Expression")


@dataclasses.dataclass
class ExpressionFolder:
    """
    Traverses this expression graph and transforms each node, from the bottom up.
    """

    fn: typing.Callable[[object], object] = lambda e: e
    typevars: TypeVarMapping = dataclasses.field(default_factory=dict)

    def __call__(self, expr: object) -> object:
        fn: typing.Callable[[object], object] = self.fn  # type: ignore
        if isinstance(expr, Expression):
            return fn(
                (replace_fn_typevars(expr.function, self.typevars))(
                    *(self(arg) for arg in expr.args),
                    **{k: self(v) for k, v in expr.kwargs.items()},
                )
            )
        return fn(expr)


@dataclasses.dataclass
class ExpressionReplacer:
    """
    Replaces certain subexpression in an expression with values.
    """

    mapping: typing.Mapping
    folder: ExpressionFolder = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self.fn)

    def __call__(self, expr):
        return self.folder(expr)

    def fn(self, o):
        return self.mapping.get(o, o)

from __future__ import annotations

import dataclasses
import typing
import typing_inspect
import functools
import inspect
from .typing_tools import *

__all__ = [
    "Expression",
    "expression",
    "ExpressionFolder",
    "ExpressionReplacer",
    "LiteralExpression",
    "E",
    "fold_identity",
    "is_expression_type",
]

T_expression = typing.TypeVar("T_expression", bound="Expression")


@dataclasses.dataclass(eq=False)
class Expression:
    """
    Subclass this type and provide relevent methods for your type. Do not add any fields.

    If the `_function` is called with `_arguments` then it should return `self`.

    The arguments should match the proper types specified in the type annotation of the function.
    The return type of the function should either be the the expression itself or
    LiteralExpression of the return type.
    """

    _function: typing.Callable
    _arguments: typing.Tuple

    def __str__(self):
        return f"{self._function.__qualname__}({', '.join(map(str, self._arguments))})"

    def __repr__(self):
        t = get_type(self)
        return f"{getattr(t, '__qualname__', t)}({self._function.__qualname__}, {repr(self._arguments)})"

    def __eq__(self, value) -> bool:
        """
        Only equal if generic types and values are equal.
        """
        if not isinstance(value, Expression):
            return False

        return (
            self._function == value._function
            and get_type(self) == get_type(value)
            and self._arguments == value._arguments
        )


T = typing.TypeVar("T")


class LiteralExpression(Expression, typing.Generic[T]):
    """
    This is meant to be used when are computing a Python value that is not an expression.
    """

    ...


E = typing.Union[T, LiteralExpression[T]]


def is_expression_type(t: typing.Type) -> bool:
    """
    Checks if a type is a subclass of expression. Also works on generic types.
    """
    return safe_issubclass(t, Expression)


def extract_literal_expression_type(
    t: typing.Type
) -> typing.Optional[typing.Type[LiteralExpression]]:
    """
    If t is a literal expression type, then it returns the literal expression type, else none.
    """
    if not typing_inspect.is_union_type(t):
        return None
    l, r = typing_inspect.get_args(t)
    l_is_expression = is_expression_type(l)
    r_is_expression = is_expression_type(r)
    if l_is_expression and r_is_expression:
        raise TypeError(f"Cannot use union of expression {t}")
    if not l_is_expression and not r_is_expression:
        return None
    return l if l_is_expression else r


def create_expression(
    fn: typing.Callable[..., T],
    args: typing.Tuple,
    return_type: typing.Optional[typing.Type[Expression]],
) -> T:
    """
    Given a function and some arguments, return the right expression for the return type.
    """
    if not return_type:
        # We need to get access to the actual function, because even though the wrapped
        # one has the same signature, the globals wont be set properly for
        # typing.inspect_type
        fn_for_typing = getattr(fn, "__wrapped__", fn)

        arg_types = [get_type(arg) for arg in args]
        return_type = infer_return_type(fn_for_typing, *arg_types)

        # If it is a literal return value, create the literal expression
        return_type = extract_literal_expression_type(return_type) or return_type

    if not is_expression_type(return_type):
        raise TypeError(f"Must return expression type not {return_type}")

    return typing.cast(T, return_type(fn, args))


T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


def n_function_args(fn: typing.Callable) -> int:
    """
    Returns the number of args a function takes, raising an error if there are any non parameter args or variable args.
    """
    n = 0
    for param in inspect.signature(fn).parameters.values():
        if param.kind != param.POSITIONAL_OR_KEYWORD:
            raise TypeError(f"Arg type of {param} not supported for function {fn}")
        n += 1
    return n


def expression(fn: T_callable) -> T_callable:
    """
    Creates an expresion object by wrapping a Python function and providing a function
    that will take in the args and return an expression of the right type.
    """
    # Note: Cannot do this because of forward type references not resolved for methods in classes

    # # Verify that it can be called with just expression types
    # inferred: typing.Type = infer_return_type(fn, *(Expression for _ in range(n_function_args(fn))))
    # inferred = extract_literal_expression_type(inferred) or inferred
    # if not typing_inspect.is_typevar(inferred) and not is_expression_type(inferred):
    #     raise TypeError(
    #         f"{fn} should return an expression type when passed in expression types, not a {inferred}"
    #     )

    @functools.wraps(fn)
    def expresion_(*args, _return_type=None):
        return create_expression(expresion_, args, _return_type)

    return typing.cast(T_callable, expresion_)


T_Expression = typing.TypeVar("T_Expression", bound="Expression")


@dataclasses.dataclass
class ExpressionFolder(typing.Generic[T]):
    """
    Traverses this expression graph and transforms each node, from the bottom up.

    You provide two functions, one to transform the leaves, and a second to transform the expressions.
    """

    value_fn: typing.Callable[[object], T]
    expression_fn: typing.Callable[
        [typing.Type[Expression], typing.Callable, typing.Tuple[T, ...]], T
    ]

    def __call__(self, expr: object):
        if isinstance(expr, Expression):
            return self.expression_fn(  # type: ignore
                get_type(expr),
                expr._function,
                tuple(self(arg) for arg in expr._arguments),
            )
        return self.value_fn(expr)  # type: ignore


fold_identity = ExpressionFolder(lambda v: v, lambda t, fn, args: t(fn, args))


@dataclasses.dataclass
class ExpressionReplacer:
    """
    Replaces certain subexpression in an expression with values.
    """

    mapping: typing.Mapping
    folder: ExpressionFolder = dataclasses.field(init=False)

    def __post_init__(self):
        self.folder = ExpressionFolder(self._value_fn, self._expression_fn)

    def __call__(self, expr):
        return self.folder(expr)

    def _value_fn(self, o):
        return self._get(o)

    def _expression_fn(self, t, fn, args):
        return self._get(t(fn, args))

    def _get(self, key):
        for actual_key, value in self.mapping.items():
            if actual_key == key:
                return value
        return key

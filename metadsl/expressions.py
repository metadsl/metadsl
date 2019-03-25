"""
An expression is a directed acyclic graph that represents some computation.

Each node in the graph has both a type and a value.

The type maps each value to some other Python value that has a user facing API
that exposes the right types.

If the value is a function call, then it has children expressions which are the arguments to that function.
Otherwise, it is any other Python value and is a leaf node.

Expression = (Type, Value)
Value = Call or other Python value
Call = (function, Expression*)

---

Defining an expression graph is seperate from deciding the meaning of that graph. You would
define this meaning by writing functions over some set of graphs that have the intended semantics you want.

The `Expressions.fold` function can be helpful here, because it gives you a way to traverse this graph.

"""

import dataclasses
import typing
import functools
import inspect


__all__ = ["Expression", "Call"]

T_callable = typing.TypeVar("T_callable", bound=typing.Callable)
T_tuple = typing.TypeVar("T_tuple", bound=typing.Tuple)


T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")

ResValue = typing.TypeVar("ResValue")
ResExpression = typing.TypeVar("ResExpression")

Instance = typing.TypeVar("Instance", covariant=True)
Value = typing.TypeVar("Value", covariant=True)

NewValue = typing.TypeVar("NewValue")

@dataclasses.dataclass(frozen=True)
class Expression(typing.Generic[Instance, Value]):
    type: typing.Callable[[Value], Instance]
    value: Value

    def replace_value(self, new_value: NewValue) -> "Expression[Instance, NewValue]":
        return dataclasses.replace(self, value=new_value)  # type: ignore

    @property
    def as_instance(self) -> Instance:
        # This type is ignored because mypy has an error
        # when having function as attributes of a dataclass.
        return self.type(self.value)  # type: ignore

    def fold(
        self,
        expr_fn: typing.Callable[["Expression"[object, ResValue]], ResExpression],
        call_value_fn: typing.Callable[["Call"[ResExpression]], ResValue],
        other_value_fn: typing.Callable[[object], ResValue],
    ) -> ResExpression:
        """
        Traverses this expression graph and transforms each node.

        All value nodes are transformed to the one type and all expression
        nodes to another type.

        You provide two functions to transform the values, which are used depending
        on whether the value is a call or not.

        Each node is transformed once, and only once, based on it's hash value

        The order in which nodes are transformed cannot be relied on.
        """

        # We memoize each function so that nodes that have multiple
        # parents are only transformed once.
        # We could define these functions globally, instead of redining them on each call,
        # but this makes sure all the caches are removed after each call.
        @functools.lru_cache(maxsize=None, typed=True)
        def fold_value(
            value: object, call_value_fn=call_value_fn, other_value_fn=other_value_fn
        ) -> ResValue:
            if isinstance(value, Call):
                return call_value_fn(
                    value.replace_args(*map(fold_expression, value.args))
                )
            return other_value_fn(value)

        @functools.lru_cache(maxsize=None, typed=True)
        def fold_expression(
            expr: Expression[object, object], expr_fn=expr_fn
        ) -> ResExpression:
            return expr_fn(expr.replace_value(fold_value(expr.value)))

        return fold_expression(self)

    def fold_expression(
        self, expr_fn: typing.Callable[["Expression"], ResExpression]
    ) -> ResExpression:
        """
        Transforms each expression, recursively, into a new expression.

        The input expression to the transformation will already have all of it's
        children transformed, if it has any.

        Each expression is transformed only once.
        """
        return self.fold(expr_fn=expr_fn, call_value_fn=lambda c: c, other_value_fn=lambda v: v)

    @property
    def as_nested_instance(self) -> Instance:
        return self.fold_expression(lambda expr: expr.as_instance)

    @property
    def as_compact(self) -> "Expression":
        """
        Combines all duplicate expression from the graph, based on the hash.
        """
        return self.fold_expression(lambda expr: expr)


Arg = typing.TypeVar("Arg")


@dataclasses.dataclass(frozen=True)
class Call(typing.Generic[Arg]):
    function: typing.Callable
    args: typing.Tuple[Arg, ...]

    def replace_args(self, *new_args: T) -> "Call[T]":
        return dataclasses.replace(self, args=tuple(new_args))  # type: ignore

    def arg_labels(self) -> typing.Iterable[str]:
        """
        Returns a list of strings for the labels of the arguments, by inspecting the function signature.
        """
        for arg_name, args in (
            inspect.signature(self.function).bind(*self.args).arguments.items()
        ):
            if isinstance(args, str):
                yield arg_name
            for i, _ in enumerate(args):
                yield f"{arg_name}:{i}"

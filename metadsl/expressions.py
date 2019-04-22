"""
This file defines a way to represent expression graphs, where the nodes
are other functions calls, if they have children, or other Python values,
if they are leaves.

It actually defines two different representations, "Expressions" and "Instances".

Expressions are basically named tuple / S-expressions, whereas instances are subclasses
of Instance that provide a Python API.
Users will interact with Instances, whereas internally we convert to expression to traverse
the graph more easily.

The graph is immutable, so to change it, we have to traverse it and create a new version.
This can be done with the `Expression.fold` method, which does a bottom up traversal.
To do a top do down traversal, you can just iterate through the Expression and Call values.
"""

import dataclasses
import typing
import functools
import inspect
import functools
from .functools import memoize

__all__ = ["Expression", "Call", "Instance", "call", "InstanceType", "instance_type"]


Arg = typing.TypeVar("Arg")

T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


@dataclasses.dataclass(frozen=True)
class Call(typing.Generic[Arg]):
    function: typing.Callable
    args: typing.Tuple[Arg, ...]

    def __repr__(self):
        return f"{self.function.__name__}({', '.join(str(a) for a in self.args)})"

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

    def map_args(self, fn: typing.Callable[[Arg], typing.Any]) -> "Call":
        return self.replace_args(*(fn(arg) for arg in self.args))

    def map_args_of(
        self, arg_type: typing.Type[Arg], fn: typing.Callable[[Arg], typing.Any]
    ) -> "Call":
        return self.replace_args(
            *(fn(arg) if isinstance(arg, arg_type) else arg for arg in self.args)
        )

    def replace_args(self, *args: typing.Any) -> "Call":
        return dataclasses.replace(self, args=args)  # type: ignore

    @staticmethod
    def decorator(
        instance_type_fn: "typing.Callable[..., InstanceType]"
    ) -> typing.Callable[[T_callable], T_callable]:
        """
        Wraps a function that takes and return instances to take create `Call` when it is called.

        For example, this:

            @Call.decorator(lambda left, right: first.__type__)
            def Or(left: T, right: T) -> T:
                ...

        Is equivalent too:

            def Or(left: T, right: T) -> T:
                instance_type_fn = lambda left, right: left.__type
                return instance_type_fn(left, right)(
                    Call(Or, (left, right))
                )

        Which is equivalent too:

            def Or(left: T, right: T) -> T:
                return left.__type__(
                    Call(Or, (left, right))
                )
        """

        def inner(fn: T_callable, instance_type_fn=instance_type_fn) -> T_callable:
            @functools.wraps(fn)
            def inner_inner(
                *args: Instance, instance_type_fn=instance_type_fn
            ) -> Instance:
                return instance_type_fn(*args)(Call(inner_inner, args))

            return typing.cast(T_callable, inner_inner)

        return inner


call = Call.decorator


Instance_ = typing.TypeVar("Instance_", bound="Instance")


@dataclasses.dataclass(frozen=True)
class Instance:
    """
    An instance is used to create a Python objects with methods around a certain instance type.

    It is useful for users.
    """

    __value__: typing.Any

    @property
    def __type__(self: Instance_) -> "InstanceType[Instance_]":
        fields = tuple(
            getattr(self, field.name)
            for field in dataclasses.fields(self)
            if field.name != "__value__"
        )
        return InstanceType(type(self), fields)

    def __repr__(self):
        return f"{repr(self.__type__)}({repr(self.__value__)})"


@dataclasses.dataclass(frozen=True)
class InstanceType(typing.Generic[Instance_]):
    type: typing.Type[Instance_]
    args: typing.Tuple

    def __call__(self, value: object) -> Instance_:
        # We have to ignore typing here, because we cannot tell MyPy
        # that the specific subtype of `Instance` we are instantiating
        # take the the arguments we have stored.
        return self.type(value, *self.args)  # type: ignore

    @classmethod
    def create(cls, type: typing.Type[Instance_], *args) -> "InstanceType[Instance_]":
        return cls(type, tuple(args))

    def __repr__(self):
        name = self.type.__name__
        if not self.args:
            return name
        return f"{name}[{', '.join(repr(arg) for arg in self.args)}]"


instance_type = InstanceType.create

ResValue = typing.TypeVar("ResValue")
ResExpression = typing.TypeVar("ResExpression")

InstanceCov = typing.TypeVar("InstanceCov", covariant=True, bound=Instance)
ValueCov = typing.TypeVar("ValueCov", covariant=True)

NewValue = typing.TypeVar("NewValue")


@dataclasses.dataclass(frozen=True)
class Expression(typing.Generic[InstanceCov, ValueCov]):
    """
    An expression is a directed acyclic graph that represents some computation.

    It has a type and a value. You can "instantiate" this expression
    by calling it's type with its value, which gives you an Instance.

    You can also go from an instance to an Expression, by using `from_instance`.

    Expression = (InstanceType, Call or other Python value)
    Call = (function, [Expression or other Python value]*)
    """

    type: typing.Callable[[ValueCov], InstanceCov]
    value: ValueCov

    def replace_value(self, new_value: NewValue) -> "Expression[InstanceCov, NewValue]":
        return dataclasses.replace(self, value=new_value)  # type: ignore

    @property
    def instance(self) -> InstanceCov:
        return self.fold_expression(lambda expr: expr._instance)

    @property
    def _instance(self) -> InstanceCov:
        # This type is ignored because mypy has an error
        # when having function as attributes of a dataclass.
        return self.type(self.value)  # type: ignore

    @classmethod
    def from_instance(cls, instance: Instance_) -> "Expression[Instance_, typing.Any]":
        """
        Recursively transforms an instance into a graph of expressions.
        """
        if isinstance(instance.__value__, Call):
            return cls(
                instance.__type__,
                instance.__value__.map_args_of(Instance, cls.from_instance),
            )
        return cls(instance.__type__, instance.__value__)

    def fold(
        self,
        expr_fn: "typing.Callable[[Expression[Instance, ResValue]], ResExpression]",
        call_value_fn: "typing.Callable[[Call[ResExpression]], ResValue]",
        other_value_fn: typing.Callable[[object], ResValue],
        other_arg_fn: typing.Callable[[object], ResExpression],
    ) -> ResExpression:
        """
        Traverses this expression graph and transforms each node.

        All value nodes are transformed to the one type and all expression
        nodes to another type.

        You provide three functions to transform the values, which are used depending
        on whether the value is a call or not.

        All values are transformed to type `ResValue ` and expression to `ResExpression`.

        The leaves are transformed first, through `other_value_fn`, which takes in a 
        Python object that is not a call and returns a `ResValue`. Then, this is passed
        to `expr_fn` which has the same type as the original expression with the value replaced
        with `ResValue`.

        Any values that are calls all have their arguments transformed like this, then
        they are passed to `call_value_fn` which has it's args now as `ResExpression`.

        Each node is transformed once, and only once, based on it's id.

        The order in which nodes are transformed cannot be relied on.
        """

        # We memoize each function so that nodes that have multiple
        # parents are only transformed once.
        # We could define these functions globally, instead of redining them on each call,
        # but this makes sure all the caches are removed after each call.
        @memoize
        def fold_value(
            value: object, call_value_fn=call_value_fn, other_value_fn=other_value_fn
        ) -> ResValue:
            if isinstance(value, Call):
                return call_value_fn(value.map_args(fold_arg))
            return other_value_fn(value)

        @memoize
        def fold_arg(
            expr: object, expr_fn=expr_fn, other_arg_fn=other_arg_fn
        ) -> ResExpression:
            if isinstance(expr, Expression):
                return expr_fn(expr.replace_value(fold_value(expr.value)))
            return other_arg_fn(expr)

        return fold_arg(self)

    def fold_expression(
        self, expr_fn: typing.Callable[["Expression"], ResExpression]
    ) -> ResExpression:
        """
        Transforms each expression, recursively, into a new expression.

        The input expression to the transformation will already have all of it's
        children transformed, if it has any.

        Each expression is transformed only once.
        """
        return typing.cast(ResExpression, self.fold(expr_fn, lambda c: c, lambda v: v, lambda a: a))

    def custom_hash(self) -> int:
        """
        Returns a hash of the expression, except if it has a non hashable value, it uses the id
        of the value instead of it's hash.
        """

        def expr_fn(expr: Expression[typing.Any, int]) -> int:
            t = expr.type  # type: ignore
            return hash((t, expr.value))

        def call_value_fn(c: Call[int]) -> int:
            return hash((c.function,) + c.args)

        def other_value_fn(o: object) -> int:
            try:
                return hash(o)
            except TypeError:
                return hash(id(o))

        return self.fold(expr_fn, call_value_fn, other_value_fn, other_value_fn)

    def compact(self) -> "Expression":
        """
        Combines all duplicate expression from the graph, based on the hash.
        """
        already_seen: typing.Dict[int, Expression] = {}

        def cached_identity(expr: Expression) -> Expression:
            """
            Identity function over expressions, that is memoized by the hash/id
            """
            h = expr.custom_hash()
            if h in already_seen:
                return already_seen[h]
            already_seen[h] = expr
            return expr

        return self.fold_expression(cached_identity)

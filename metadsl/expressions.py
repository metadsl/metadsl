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

---

An instance is how you can take a particular expression and create a usable end user experience around it.
"""

import dataclasses
import typing
import functools
import inspect
import functools

__all__ = ["Expression", "Call", "Instance", "call", "InstanceType", "instance_type"]


Arg = typing.TypeVar("Arg")
NewArg = typing.TypeVar("NewArg")

T_callable = typing.TypeVar("T_callable", bound=typing.Callable)


@dataclasses.dataclass(frozen=True)
class Call(typing.Generic[Arg]):
    function: typing.Callable
    args: typing.Tuple[Arg, ...]

    def __str__(self):
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

    def map_args(self, fn: typing.Callable[[Arg], NewArg]) -> "Call[NewArg]":
        return dataclasses.replace(self, args=tuple(map(fn, self.args)))  # type: ignore

    @staticmethod
    def decorator(
        instance_type_fn: "typing.Callable[..., InstanceType]"
    ) -> typing.Callable[[T_callable], T_callable]:
        """
        Wraps a function that takes and return instances to take create `Call` when it is called.

        For example, this:

            @Call.decorator(lambda first, second: first)
            def Or(left: T, right: T) -> T:
                ...

        Is equivalent too:

            def Or(left: T, right: T) -> T:
                instance_type_fn = lambda first, second: first
                return instance_type_fn(left, right).__type__(
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
                *args: Instance, fn=fn, instance_type_fn=instance_type_fn
            ) -> Instance:
                instance_type = instance_type_fn(*(arg.__type__ for arg in args))
                return instance_type(Call(fn, tuple(args)))

            return typing.cast(T_callable, inner_inner)

        return inner


call = Call.decorator


Instance_ = typing.TypeVar("Instance_", bound="Instance")


@dataclasses.dataclass(frozen=True)
class Instance:
    __value__: typing.Any

    @property
    def __type__(self: Instance_) -> "InstanceType[Instance_]":
        fields = tuple(
            getattr(self, field.name)
            for field in dataclasses.fields(self)
            if field.name != "__value__"
        )
        return InstanceType(type(self), fields)

    def __str__(self):
        return f"{self.__type__}({self.__value__})"


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

    def __str__(self):
        name = self.type.__name__
        if not self.args:
            return name
        return f"{self.type.__name__}[{', '.join(str(arg) for arg in self.args)}]"


instance_type = InstanceType.create

ResValue = typing.TypeVar("ResValue")
ResExpression = typing.TypeVar("ResExpression")

InstanceCov = typing.TypeVar("InstanceCov", covariant=True, bound=Instance)
ValueCov = typing.TypeVar("ValueCov", covariant=True)

NewValue = typing.TypeVar("NewValue")


@dataclasses.dataclass(frozen=True)
class Expression(typing.Generic[InstanceCov, ValueCov]):
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
        if not isinstance(instance.__value__, Call):
            return cls._from_instance(instance)
        value = instance.__value__
        new_value = value.map_args(cls.from_instance)
        return cls._from_instance(dataclasses.replace(instance, __value__=new_value))

    @classmethod
    def _from_instance(cls, instance: Instance_) -> "Expression[Instance_, typing.Any]":
        return cls(instance.__type__, instance.__value__)

    def fold(
        self,
        expr_fn: "typing.Callable[[Expression[Instance, ResValue]], ResExpression]",
        call_value_fn: "typing.Callable[[Call[ResExpression]], ResValue]",
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
                return call_value_fn(value.map_args(fold_expression))
            return other_value_fn(value)

        @functools.lru_cache(maxsize=None, typed=True)
        def fold_expression(
            expr: Expression[Instance, object], expr_fn=expr_fn
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
        return self.fold(
            expr_fn=expr_fn, call_value_fn=lambda c: c, other_value_fn=lambda v: v
        )

    def compact(self) -> "Expression":
        """
        Combines all duplicate expression from the graph, based on the hash.
        """
        return self.fold_expression(lambda expr: expr)

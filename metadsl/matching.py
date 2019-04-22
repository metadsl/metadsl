"""
Pattern matching allows you to define replacement rules by creating a template that should resemble
an expression, with certain leaf nodes as Wildcards. These can match any node in the target expression.

The values at these wildcards are captured and passed to another function to compute a resulting expression
to use as the replacement.

Conceptually, this is similar to regular expression matching / finite state transducers. Technically,
this is a form of symbolic tree transducers, but not implemented in a mathematically consistant way. If it was,
then we could more easily combine matches to make them execute faster and compute properties about them.
"""

import typing
import dataclasses
import inspect
from .expressions import Expression, Call, Instance

from .rules import Rule

__all__ = ["match_rule", "MatchFunctionType"]

T = typing.TypeVar("T", bound=Instance)

MatchFunctionType = typing.Callable[
    ..., typing.Tuple[T, typing.Callable[[], typing.Optional[T]]]
]


def match_rule(match_function: MatchFunctionType) -> Rule:
    """
    Creates a replacement rule given a function that maps from wildcard inputs
    to two things, a template expression tree and a replacement thunk.

    If the template matches an expression, it will be replaced with the result of the thunk, replacing
    the input args with the nodes at their locations in the template.

    You can also return None from the rule to signal that it won't match.
    """
    return InferredMatchRule(match_function)


@dataclasses.dataclass(eq=False)
class Wildcard:
    """
    Insert this somewhere in an expression tree to represent any expression or value.
    """

    pass


@dataclasses.dataclass
class MatchRule:
    template: typing.Union[Expression, Wildcard]
    match: typing.Callable[[typing.Dict[Wildcard, object]], typing.Optional[Expression]]

    def __call__(self, expr: Expression) -> typing.Optional[Expression]:
        wildcards_to_nodes = match_expression(self.template, expr)
        if wildcards_to_nodes is None:
            return None
        return self.match(wildcards_to_nodes)  # type: ignore


@dataclasses.dataclass
class InferredMatchRule(typing.Generic[T]):
    match_function: MatchFunctionType
    match_rule: MatchRule = dataclasses.field(init=False)
    arg_wildcards: typing.Tuple[Wildcard] = dataclasses.field(init=False)

    def __post_init__(self):
        # Create one wildcard` per argument
        self.arg_wildcards = tuple(
            Wildcard() for _ in range(n_function_args(self.match_function))
        )

        # Call the function first to create a template with the wildcards
        template, _ = self.match_function(*self.arg_wildcards)

        self.match_rule = MatchRule(Expression.from_instance(template), self._match)

    def _match(
        self, wildcards_to_args: typing.Dict[Wildcard, object]
    ) -> typing.Optional[Expression]:
        assert len(self.arg_wildcards) == len(wildcards_to_args)
        args = [wildcards_to_args[wildcard] for wildcard in self.arg_wildcards]
        # TODO: Replace `instance` property with function that does the instance check
        _, instance_think = self.match_function(*(arg.instance if isinstance(arg, Expression) else arg for arg in args))  # type: ignore
        instance: typing.Optional[Instance] = instance_think()
        if instance is None:
            return None
        return Expression.from_instance(instance)

    def __call__(self, expr: Expression) -> typing.Optional[Expression]:
        return self.match_rule(expr)


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


WilcardMapping = typing.Optional[typing.Dict[Wildcard, object]]


def match_expression(template: object, expr: object) -> WilcardMapping:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.

    Mutally recursive with match_value
    """
    if isinstance(template, Wildcard):
        return {template: expr}
    if isinstance(expr, Expression):
        if not isinstance(template, Expression) or template.type != expr.type:
            return None
        return match_value(template.value, expr.value)
    return {} if template == expr else None


def match_value(template: object, value: object) -> WilcardMapping:
    if isinstance(template, Wildcard):
        return {template: value}

    # If we are dealing with a call, verify it matches template and recurse
    if isinstance(value, Call):
        if not isinstance(template, Call) or value.function != template.function:
            return None

        return combine_mappings(
            *(
                match_expression(arg_template, arg_value)
                for arg_template, arg_value in zip(template.args, value.args)
            )
        )

    # If we are dealing with a non call value, make sure they are equal
    return {} if template == value else None


def combine_mappings(*mappings: WilcardMapping) -> WilcardMapping:
    """
    Combing mappings by merging the dictionaries, and returning None if any of them are None.

    If any keys duplicate and they are not equal, None is also returned.
    """
    res: typing.Dict[Wildcard, object] = {}
    for mapping in mappings:
        if mapping is None:
            return None
        for key, value in mapping.items():
            if key in res:
                if res[key] != value:
                    return None
            else:
                res[key] = value
    return res


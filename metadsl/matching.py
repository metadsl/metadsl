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

# import inspect
from .calls import *
from .expressions import *

from .rules import Rule

__all__ = ["match_rule", "pure_match_rule", "MatchFunctionType", "ArgType", "ArgTypes"]

T = typing.TypeVar("T")

PureFunctionType = typing.Callable[..., typing.Tuple[T, T]]
MatchFunctionType = typing.Callable[
    ..., typing.Tuple[T, typing.Callable[[], typing.Optional[T]]]
]
ArgType = typing.Optional[typing.Callable[["Wildcard"], Instance]]
ArgTypes = typing.Tuple[ArgType, ...]


def pure_match_rule(arg_types: ArgTypes, pure_match_function: PureFunctionType) -> Rule:
    return InferredPureMatchRule(arg_types, pure_match_function)


def match_rule(arg_types: ArgTypes, match_function: MatchFunctionType) -> Rule:
    """
    Creates a replacement rule given a function that maps from wildcard inputs
    to two things, a template expression tree and a replacement thunk.

    If the template matches an expression, it will be replaced with the result of the thunk, replacing
    the input args with the nodes at their locations in the template.

    You can also return None from the rule to signal that it won't match.
    """
    return InferredMatchRule(arg_types, match_function)


@dataclasses.dataclass(eq=False)
class Wildcard:
    """
    Insert this somewhere in an expression tree to represent any expression or value.
    """

    pass


# TODO: Wrap wildcard in call so that it is proper in an instance.
# T_Instance = typing.TypeVar("T_Instance", bound="Instance")


# @call(lambda wildcard, type: type)
# def create_wildcard(
#     wildcard: Wildcard, type: typing.Callable[[Wildcard], T_Instance]
# ) -> T_Instance:
#     ...


@dataclasses.dataclass
class MatchRule:
    template: ExpressionType
    match: typing.Callable[
        [typing.Dict[Wildcard, object]], typing.Optional[ExpressionType]
    ]

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        wildcards_to_nodes = match_expression(self.template, expr)
        if wildcards_to_nodes is None:
            return None
        return self.match(wildcards_to_nodes)  # type: ignore


@dataclasses.dataclass
class InferredPureMatchRule:
    # TODO: Remove these from call, just need in init.
    arg_types: ArgTypes
    pure_match_function: PureFunctionType
    match_rule: MatchRule = dataclasses.field(init=False)
    result: ExpressionType = dataclasses.field(init=False)

    def __post_init__(self):
        arg_wildcards = tuple(Wildcard() for t in self.arg_types)

        template, result = self.pure_match_function(
            *(t(w) if t else w for t, w in zip(self.arg_types, arg_wildcards))
        )
        self.result = to_expression(result)
        self.match_rule = MatchRule(to_expression(template), self._match)

    def _match(
        self, wildcards_to_args: typing.Dict[Wildcard, object]
    ) -> typing.Optional[ExpressionType]:
        return expression_replacer(tuple(wildcards_to_args.items()))(self.result)

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        return self.match_rule(expr)

@dataclasses.dataclass
class InferredMatchRule(typing.Generic[T]):
    arg_types: ArgTypes
    match_function: MatchFunctionType
    match_rule: MatchRule = dataclasses.field(init=False)
    arg_wildcards: typing.Tuple[Wildcard, ...] = dataclasses.field(init=False)

    def __post_init__(self):
        # Create one wildcard` per argument
        self.arg_wildcards = tuple(Wildcard() for t in self.arg_types)

        # Call the function first to create a template with the wildcards
        template, _ = self.match_function(
            *(t(w) if t else w for t, w in zip(self.arg_types, self.arg_wildcards))
        )

        self.match_rule = MatchRule(to_expression(template), self._match)

    def _match(
        self, wildcards_to_args: typing.Dict[Wildcard, object]
    ) -> typing.Optional[ExpressionType]:
        assert len(self.arg_wildcards) == len(wildcards_to_args)
        args = [wildcards_to_args[wildcard] for wildcard in self.arg_wildcards]

        _, instance_think = self.match_function(
            *map(from_expression, args)  # type: ignore
        )
        instance = instance_think()
        if instance is None:
            return None
        return to_expression(instance)

    def __call__(self, expr: ExpressionType) -> typing.Optional[ExpressionType]:
        return self.match_rule(expr)


# def n_function_args(fn: typing.Callable) -> int:
#     """
#     Returns the number of args a function takes, raising an error if there are any non parameter args or variable args.
#     """
#     n = 0
#     for param in inspect.signature(fn).parameters.values():
#         if param.kind != param.POSITIONAL_OR_KEYWORD:
#             raise TypeError(f"Arg type of {param} not supported for function {fn}")
#         n += 1
#     return n


WilcardMapping = typing.Optional[typing.Dict[Wildcard, object]]


def match_expression(template: object, expr: object) -> WilcardMapping:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.

    Mutally recursive with match_value
    """
    if isinstance(template, Wildcard):
        return {template: expr}
    if isinstance(expr, RecursiveCall):
        if (
            not isinstance(template, RecursiveCall)
            or template.function != expr.function
        ):
            return None
        return combine_mappings(
            *(
                match_expression(arg_template, arg_value)
                for arg_template, arg_value in zip(template.args, expr.args)
            )
        )

    return {} if template == expr else None


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


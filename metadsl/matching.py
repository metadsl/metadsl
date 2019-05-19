"""
Pattern matching allows you to define replacement rules by creating a template that should resemble
an expression, with certain leaf nodes as Wildcards. These can match any node in the target expression.

The values at these wildcards are captured and passed to another function to compute a resulting expression
to use as the replacement.

Conceptually, this is similar to regular expression matching / finite state transducers. Technically,
this is a form of symbolic tree transducers, but not implemented in a mathematically consistant way. If it was,
then we could more easily combine matches to make them execute faster and compute properties about them. This would
be good to add at a later date, and could be done without having users change their code.
"""

import typing
import dataclasses

# import inspect
from .expressions import *
from .dict_tools import *
from .typing_tools import *
from .rules import Rule

__all__ = ["create_wildcard", "extract_wildcard", "Wildcard", "rule"]

T = typing.TypeVar("T", bound=Expression)


# Mapping from wildcards to the matching pattern and replacement
MatchFunctionType = typing.Callable[..., typing.Tuple[T, typing.Optional[T]]]


def rule(fn: MatchFunctionType) -> Rule:
    """
    Creates a new rule given a callable that accepts wildcards and returns
    the match value and the replacement value.
    """

    return InferredMatchRule(fn)


@dataclasses.dataclass(eq=False)
class Wildcard(typing.Generic[T]):
    """
    Insert this somewhere in an expression tree to represent any expression or value of type T.
    """


@expression
def wildcard(wildcard: E[Wildcard[T]]) -> T:
    ...


def create_wildcard(t: typing.Type[T]) -> T:
    """
    Returns a wildcard of type "t"
    """
    return wildcard(Wildcard[t]())  # type: ignore


def extract_wildcard(o: object) -> typing.Optional[Wildcard]:
    """
    Returns a wildcard, if the expression was created from one, or else None.
    """
    if not isinstance(o, Expression):
        return None
    if o.function != wildcard:
        return None
    return typing.cast(Wildcard, o.args[0])


# a number of (wildcard expression, replacement) pairs
WildcardMapping = typing.Mapping[Expression, object]


@dataclasses.dataclass
class MatchRule:
    """
    Creates a replacement rule given a function that maps from wildcard inputs
    to two things, a template expression tree and a replacement thunk.

    If the template matches an expression, it will be replaced with the result of the thunk, replacing
    the input args with the nodes at their locations in the template.

    You can also return None from the rule to signal that it won't match.
    """

    # the wildcards that are present in the template
    wildcards: typing.List[Expression]

    # expression containing wildcard expression it that will be matched against the
    # incoming expression
    template: object
    # function that takes a mapping of wildcard expression to their replacements
    # and return a new object
    match: typing.Callable[[WildcardMapping], typing.Optional[object]]

    def __call__(self, expr: object) -> typing.Optional[object]:
        try:
            wildcards_to_nodes = match_expression(self.wildcards, self.template, expr)
        except ValueError:
            return None
        return self.match(wildcards_to_nodes)  # type: ignore


@dataclasses.dataclass
class InferredMatchRule(typing.Generic[T]):
    matchfunction: MatchFunctionType
    match_rule: MatchRule = dataclasses.field(init=False)
    result: typing.Optional[Expression] = dataclasses.field(init=False)

    def __post_init__(self):
        # Create one wildcard` per argument
        wildcards = [create_wildcard(a) for a in get_arg_hints(self.matchfunction)]

        # Call the function first to create a template with the wildcards
        template, self.result = self.matchfunction(*wildcards)

        self.match_rule = MatchRule(wildcards, template, self._match)

    def _match(self, wildcards_to_args: WildcardMapping) -> typing.Optional[object]:
        if self.result is not None:
            return ExpressionReplacer(wildcards_to_args)(self.result)

        args = (wildcards_to_args[wildcard] for wildcard in self.match_rule.wildcards)

        _, expression = self.matchfunction(*args)
        return expression

    def __call__(self, expr: object) -> typing.Optional[object]:
        return self.match_rule(expr)


def match_expression(
    wildcards: typing.List[Expression], template: object, expr: object
) -> WildcardMapping:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.

    Mutally recursive with match_value
    """
    if template in wildcards:
        return UnhashableMapping(Item(typing.cast(Expression, template), expr))
    if isinstance(expr, Expression):
        if not isinstance(template, Expression) or template.function != expr.function:
            raise ValueError

        # TODO: Verify same # of args and same kwargs
        # TODO: march kwargs
        # TODO: Add *args matching
        # matched_args = (
        #         match_expression(wildcards, arg_template, arg_value)
        #         for arg_template, arg_value in zip(template.args, expr.args)
        #     )
        # matched_kwargs = for k, v in 
        # return safe_merge(
        #     *(
        #         match_expression(wildcards, arg_template, arg_value)
        #         for arg_template, arg_value in zip(template.args, expr.args)
        #     ),
        #     dict_constructor=UnhashableMapping
        # )
    if template != expr:
        raise ValueError
    return UnhashableMapping()

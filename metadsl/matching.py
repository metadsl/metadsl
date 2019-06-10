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

__all__ = ["create_wildcard", "Wildcard", "rule", "R"]

T = typing.TypeVar("T", bound=Expression)

R = typing.Tuple[T, typing.Callable[[], typing.Optional[T]]]
# Mapping from wildcards to the matching pattern and replacement
MatchFunctionType = typing.Callable[..., R]


def rule(fn: MatchFunctionType) -> Rule:
    """
    Creates a new rule given a callable that accepts wildcards and returns
    the match value and the replacement value.
    """

    return MatchRule(fn)


class Wildcard(Expression, typing.Generic[T]):
    """
    Insert this somewhere in an expression tree to represent any expression or value of type T.
    """


@expression
def create_wildcard_expession(t: typing.Type[T], obj: object) -> T:
    """
    The object inside is only needed for identity checks, to different
    two wildcards if the objects are different.
    """
    ...


def create_wildcard(t: typing.Type[T]) -> T:
    """
    Returns a wildcard of type "t"
    """
    return create_wildcard_expession(t, object())


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

    matchfunction: MatchFunctionType

    # the wildcards that are present in the template
    wildcards: typing.List[Expression] = dataclasses.field(init=False)

    # expression containing wildcard expression it that will be matched against the
    # incoming expression
    template: object = dataclasses.field(init=False)

    def __post_init__(self):
        # Create one wildcard` per argument
        self.wildcards = [create_wildcard(a) for a in get_arg_hints(self.matchfunction)]

        # Call the function first to create a template with the wildcards
        self.template, _ = self.matchfunction(*self.wildcards)

    def __call__(self, expr: object) -> typing.Optional[object]:
        try:
            wildcards_to_nodes = match_expression(self.wildcards, self.template, expr)
        except ValueError:
            return None
        args = [wildcards_to_nodes[wildcard] for wildcard in self.wildcards]

        _, expression_thunk = self.matchfunction(*args)
        return expression_thunk()


def match_expression(
    wildcards: typing.List[Expression], template: object, expr: object
) -> WildcardMapping:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.
    """

    if template in wildcards:
        return UnhashableMapping(Item(typing.cast(Expression, template), expr))

    if isinstance(expr, Expression):
        if (
            not isinstance(template, Expression)
            or expr.function != template.function
            or len(expr.args) != len(template.args)
            or set(expr.kwargs.keys()) != set(template.kwargs.keys())
        ):
            raise ValueError

        # TODO: Add *args matching

        return safe_merge(
            *(
                match_expression(wildcards, arg_template, arg_value)
                for arg_template, arg_value in zip(template.args, expr.args)
            ),
            *(
                match_expression(wildcards, template.kwargs[key], expr.kwargs[key])
                for key in template.kwargs.keys()
            ),
            dict_constructor=UnhashableMapping
        )
    if template != expr:
        raise ValueError
    return UnhashableMapping()

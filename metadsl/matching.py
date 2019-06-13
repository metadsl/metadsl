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
from .rules import Rule, NoMatch

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
        typevars, wildcards_to_nodes = match_expression(  # type: ignore
            self.wildcards, self.template, expr
        )

        args = [wildcards_to_nodes[wildcard] for wildcard in self.wildcards]

        _, expression_thunk = self.matchfunction(*args)
        # Replace typevars in resualt with their matched values
        return ExpressionFolder(lambda e: e, lambda tp: replace_typevars(typevars, tp))(
            expression_thunk()
        )


def collapse_tuple(t: typing.Tuple, l: int, r: int) -> typing.Tuple:
    """
    Collapses the middle of a tuple into another nested tuple, keeping l on the left side
    uncollapsed and r on the right side un collapsed

    >>> collapse_tuple(tuple(range(10)), 3, 4)
    (0, 1, 2, (3, 4, 5), 6, 7, 8, 9)
    >>> collapse_tuple(tuple(range(5)), 3, 0)
    (0, 1, 2, (3, 4))
    """
    if r == 0:
        return tuple([*t[:l], t[l:]])
    return tuple([*t[:l], t[l:-r], *t[-r:]])


def match_expression(
    wildcards: typing.List[Expression], template: object, expr: object
) -> typing.Tuple[TypeVarMapping, WildcardMapping]:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.
    """

    if template in wildcards:
        # Match type of wildcard with type of expression
        return (
            match_values(template, expr),
            UnhashableMapping(Item(typing.cast(Expression, template), expr)),
        )

    if isinstance(expr, Expression):
        if not isinstance(template, Expression):
            raise NoMatch
        try:
            fn_typevar_mappings: TypeVarMapping = match_functions(
                template.function, expr.function
            )
        except TypeError:
            raise NoMatch

        if set(expr.kwargs.keys()) != set(template.kwargs.keys()):
            raise TypeError("Wrong kwargs in match")

        template_args: typing.Iterable[object]
        expr_args: typing.Iterable[object]

        # Process args in the template that can represent any number of args.
        # These are the "IteratedPlaceholder"s
        # Allow one iterated placeholder in the template args
        # For example fn(a, b, [...], *c, d, e, [...])
        # Here `c` should take as many args as it can between the ends,
        # Each of those should be matched against the inner
        iterated_args = [
            arg for arg in template.args if isinstance(arg, IteratedPlaceholder)
        ]
        if iterated_args:
            # template args, minus the iterator, is the minimum length of the values
            # If they have less values than this, raise an error
            if len(expr.args) < len(template.args) - 1:
                raise TypeError("Wrong number of args in match")
            template_args_ = list(template.args)
            # Only support one iterated arg for now
            # TODO: Support more than one, would require branching
            template_iterated, = iterated_args
            template_index_iterated = list(template.args).index(template_iterated)

            # Swap template iterated with inner wildcard
            template_args_[template_index_iterated], = template_iterated.args
            template_args = template_args_

            expr_args = collapse_tuple(
                expr.args,
                template_index_iterated,
                # The number we should preserve on the right, is the number of template
                # args after index
                len(template.args) - template_index_iterated - 1,
            )

        else:
            if len(template.args) != len(expr.args):
                raise TypeError("Wrong number of args in match")
            template_args = template.args
            expr_args = expr.args

        type_mappings, expr_mappings = zip(
            *(
                match_expression(wildcards, arg_template, arg_value)
                for arg_template, arg_value in zip(template_args, expr_args)
            ),
            *(
                match_expression(wildcards, template.kwargs[key], expr.kwargs[key])
                for key in template.kwargs.keys()
            )
        )
        return (
            safe_merge(
                fn_typevar_mappings, *type_mappings, dict_constructor=UnhashableMapping
            ),
            safe_merge(*expr_mappings, dict_constructor=UnhashableMapping),
        )
    if template != expr:
        raise NoMatch
    return match_values(template, expr), UnhashableMapping()

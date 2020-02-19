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
import functools
import types
import inspect
import typing_inspect
import functools

from .expressions import *
from .dict_tools import *
from .normalized import *
from .typing_tools import *
from .rules import Rule, Replacement


__all__ = ["R", "NoMatch", "rule", "default_rule", "create_wildcard"]

T = typing.TypeVar("T", bound=Expression)

R_single = typing.Tuple[T, typing.Union[typing.Callable[[], T], T]]
R = typing.Union[typing.Generator[R_single[T], None, None], R_single[T]]
# Mapping from wildcards to the matching pattern and replacement
MatchFunctionType = typing.Callable[..., R[T]]


class NoMatch(Exception):
    pass


def rule(fn: MatchFunctionType) -> Rule:
    """
    Creates a new rule given a callable that accepts wildcards and returns
    the match value and the replacement value.
    """

    return MatchRule(fn)


T_Callable = typing.TypeVar("T_Callable", bound=typing.Callable)


def default_rule(fn: typing.Callable) -> Rule:
    """
    Creates a rule based on the body of a passed in expression function
    """
    return DefaultRule(fn)


@dataclasses.dataclass
class DefaultRule:
    fn: typing.Callable
    inner_fn: typing.Callable = dataclasses.field(init=False, repr=False)

    def __str__(self):
        return f"{self.inner_fn.__module__}.{self.inner_fn.__qualname__}"

    def __post_init__(self):
        self.inner_fn = self.fn.__wrapped__  # type: ignore

    def __call__(self, ref: ExpressionReference) -> typing.Iterable[Replacement]:
        """
        This rule should match whenever the expression is this function.

        Then, all it has to do is get the type variable mapping given the current args
        and apply it to the return value. This is so that if the body uses generic type
        variables, they are turned into the actual instantiations. 
        """
        expr = ref.expression
        if not isinstance(expr, Expression):
            return

        fn = self.fn

        args = expr.args

        # If any of the args are placeholders, don't match!
        if any(
            isinstance(arg, PlaceholderExpression)
            for arg in args + list(expr.kwargs.values())
        ):
            return None

        typevars: TypeVarMapping = infer_return_type(
            expr.function.fn,  # type: ignore
            getattr(expr.function, "owner", None),
            getattr(expr.function, "is_classmethod", False),
            tuple(args),
            expr.kwargs,
        )[-1]
        if isinstance(fn, BoundInfer) and isinstance(expr.function, BoundInfer):
            if fn.fn != expr.function.fn:
                return None
            if fn.is_classmethod:
                args = [
                    typing.cast(object, replace_typevars(typevars, fn.owner))
                ] + args

        elif fn != expr.function:
            return None
        with TypeVarScope(*typevars.keys()):
            new_expr = self.inner_fn(*args, **expr.kwargs)
            result = ReplaceTypevarsExpression(typevars)(new_expr)
        ref.replace(result)
        yield Replacement(str(self))


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

    results: typing.List[R] = dataclasses.field(init=False)

    def __str__(self):
        return f"{self.matchfunction.__module__}.{self.matchfunction.__qualname__}"

    def __post_init__(self):
        functools.update_wrapper(self, self.matchfunction)
        # Create one wildcard` per argument
        self.wildcards = [create_wildcard(a) for a in get_arg_hints(self.matchfunction)]

        # Call the function first to create a template with the wildcards
        result = self.matchfunction(*self.wildcards)
        self.results = (
            list(result)  # type: ignore
            if inspect.isgeneratorfunction(self.matchfunction)
            else [result]
        )

    def __call__(self, ref: ExpressionReference) -> typing.Iterable[Replacement]:
        expr = ref.expression
        for i, result in enumerate(self.results):
            template, _ = result
            try:
                typevars, wildcards_to_nodes = match_expression(  # type: ignore
                    self.wildcards, template, expr
                )
            except NoMatch:
                continue

            args = [
                wildcards_to_nodes.get(wildcard, wildcard)
                for wildcard in self.wildcards
            ]
            _, expression_thunk = (
                list(self.matchfunction(*args))[i]
                if inspect.isgeneratorfunction(self.matchfunction)
                else self.matchfunction(*args)
            )
            try:
                result_expr: object = (
                    expression_thunk()
                    if isinstance(expression_thunk, types.FunctionType)
                    else expression_thunk
                )
            except NoMatch:
                continue
            with TypeVarScope(*typevars.keys()):
                result_expr = ReplaceTypevarsExpression(typevars)(result_expr)
                ref.replace(result_expr)
            yield Replacement(str(self))
            return


@dataclasses.dataclass(frozen=True)
class ReplaceTypevarsExpression:
    """
    Use a class instead of a function so we can partially apply it and have equality based on typevars 
    """

    typevars: TypeVarMapping

    def __call__(self, expression: object) -> object:
        """
        Replaces all typevars found in the classmethods of an expression.
        """
        typevars = self.typevars
        if isinstance(expression, Expression):
            new_args = [self(a) for a in expression.args]
            new_kwargs = {k: self(v) for k, v in expression.kwargs.items()}
            new_fn = replace_fn_typevars(expression.function, typevars)
            return replace_typevars(
                typevars, typing_inspect.get_generic_type(expression)
            )(new_fn, new_args, new_kwargs)
        return replace_fn_typevars(
            expression,
            typevars,
            ReplaceTypevarsExpression(typevars=HashableMapping(typevars)),
        )


def match_expression(
    wildcards: typing.List[Expression], template: object, expr: object
) -> typing.Tuple[TypeVarMapping, WildcardMapping]:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    template: the expression with wildcards in it
    expr: the expression without wildcards to match against

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.
    """
    if template in wildcards:
        # If we are matching against a placeholder and the expression is not resolved to that placeholder, don't match.
        if (
            isinstance(template, PlaceholderExpression)
            and isinstance(expr, Expression)
            and not typing_inspect.is_typevar(
                typing_inspect.get_args(typing_inspect.get_generic_type(template))[0]
            )
        ):
            raise NoMatch

        # Match type of wildcard with type of expression
        try:
            return (
                match_values(template, expr),
                UnhashableMapping(Item(typing.cast(Expression, template), expr)),
            )
        except TypeError:
            raise NoMatch

    if isinstance(expr, Expression):
        if not isinstance(template, Expression):
            raise NoMatch
        # Any typevars in the template that are unbound should be matched with their
        # versions in the expr

        try:
            fn_type_mapping: TypeVarMapping = match_functions(
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
            # Only support one iterated arg for now
            # TODO: Support more than one, would require branching
            assert len(iterated_args) == 1
            # template args, minus the iterators, is the minimum length of the values
            # If they have less values than this, raise an error
            min_n_args = len(template.args) - 1
            if len(expr.args) < min_n_args:
                raise NoMatch("Wrong number of args in match")
            template_args_ = list(template.args)
            (template_iterated,) = iterated_args
            template_index_iterated = list(template.args).index(template_iterated)

            # Swap template iterated with inner wildcard
            (template_args_[template_index_iterated],) = template_iterated.args
            template_args = template_args_

            expr_args = collapse_tuple(
                tuple(expr.args),
                template_index_iterated,
                # The number we should preserve on the right, is the number of template
                # args after index
                len(template.args) - template_index_iterated - 1,
            )

        else:
            if len(template.args) != len(expr.args):
                raise NoMatch("Wrong number of args in match")
            template_args = template.args
            expr_args = expr.args

        type_mappings, expr_mappings = list(
            zip(
                *(
                    match_expression(wildcards, arg_template, arg_value)
                    for arg_template, arg_value in zip(template_args, expr_args)
                ),
                *(
                    match_expression(wildcards, template.kwargs[key], expr.kwargs[key])
                    for key in template.kwargs.keys()
                ),
            )
        ) or ((), ())
        try:
            merged_typevars: TypeVarMapping = merge_typevars(
                fn_type_mapping, *type_mappings
            )
        except TypeError:
            raise NoMatch
        try:
            return (
                merged_typevars,
                safe_merge(*expr_mappings, dict_constructor=UnhashableMapping),
            )
        except ValueError:
            raise NoMatch
    if template != expr:
        raise NoMatch
    return match_values(template, expr), UnhashableMapping()


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

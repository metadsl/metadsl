"""
Pattern matching allows you to define replacement strategies by creating a template that should resemble
an expression, with certain leaf nodes as Wildcards. These can match any node in the target expression.

The values at these wildcards are captured and passed to another function to compute a resulting expression
to use as the replacement.

Conceptually, this is similar to regular expression matching / finite state transducers. Technically,
this is a form of symbolic tree transducers, but not implemented in a mathematically consistant way. If it was,
then we could more easily combine matches to make them execute faster and compute properties about them. This would
be good to add at a later date, and could be done without having users change their code.
"""
from __future__ import annotations

import dataclasses
import functools
import inspect
import logging
import types
import typing

import typing_inspect
from metadsl import *
from metadsl.typing_tools import *

from .strategies import *

__all__ = ["R", "NoMatch", "rule", "default_rule", "create_wildcard"]

T = typing.TypeVar("T")

R = typing.Union[
    typing.Tuple[T, typing.Union[typing.Callable[[], T], T]],
    typing.Generator[
        typing.Tuple[T, typing.Union[typing.Callable[[], T], T]], None, None
    ],
]
# Mapping from wildcards to the matching pattern and replacement
MatchFunctionType = typing.Callable[..., R]

logger = logging.getLogger(__name__)


class NoMatch(Exception):
    pass


def rule(fn: MatchFunctionType) -> Strategy:
    """
    Creates a new strategy given a callable that accepts wildcards and returns
    the match value and the replacement value.
    """

    return Rule(fn)


T_Callable = typing.TypeVar("T_Callable", bound=typing.Callable)


def default_rule(fn: typing.Callable) -> Strategy:
    """
    Creates a strategy based on the body of a passed in expression function
    """
    return DefaultRule(fn)


@dataclasses.dataclass(unsafe_hash=True)
class DefaultRule(Strategy):
    fn: typing.Callable
    inner_fn: typing.Callable = dataclasses.field(
        init=False, repr=False, compare=False, hash=False
    )

    def __str__(self):
        return f"{self.inner_fn.__module__}.{self.inner_fn.__qualname__}"

    def __post_init__(self):
        self.inner_fn = self.fn.__wrapped__  # type: ignore

    def optimize(self, executor, strategy):
        # TODO: Implement optimizations for default rules
        pass

    def __call__(self, ref: ExpressionReference) -> typing.Iterable[Result]:
        """
        This strategy should match whenever the expression is this function.

        Then, all it has to do is get the type variable mapping given the current args
        and apply it to the return value. This is so that if the body uses generic type
        variables, they are turned into the actual instantiations. 
        """
        with CaptureLogging() as results:
            expr = ref.expression
            logger.debug("DefaultRule.__call__ self=%s expr=%s", self, expr)
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
            logger.debug("DefaultRule.__call__ result=%s", result)

            ref.replace(result)
        yield Result(str(self), logs="\n".join(results))


class Wildcard(Expression, typing.Generic[T]):
    """
    Insert this somewhere in an expression tree to represent any expression or value of type T.
    """

    @expression
    @classmethod
    def create(cls, obj: object) -> T:
        """
        The object inside is only needed for identity checks, to different
        two wildcards if the objects are different.
        """
        ...


def create_wildcard(t: typing.Type[T]) -> T:
    """
    Returns a wildcard of type "t"
    """
    return Wildcard[t].create(object())  # type: ignore


# a number of (wildcard expression, replacement) pairs
WildcardMapping = typing.Mapping[Expression, object]


@dataclasses.dataclass(unsafe_hash=True)
class Rule(Strategy):
    """
    Creates a replacement strategy given a function that maps from wildcard inputs
    to two things, a template expression tree and a replacement thunk.

    If the template matches an expression, it will be replaced with the result of the thunk, replacing
    the input args with the nodes at their locations in the template.

    You can also return None from the strategy to signal that it won't match.
    """

    matchfunction: MatchFunctionType

    # the wildcards that are present in the template
    wildcards: typing.List[Expression] = dataclasses.field(
        init=False, hash=False, compare=False
    )

    results: typing.List[R] = dataclasses.field(init=False, hash=False, compare=False)

    def __str__(self):
        return f"{self.matchfunction.__module__}.{self.matchfunction.__qualname__}"

    def __post_init__(self):
        functools.update_wrapper(self, self.matchfunction)
        # Create one wildcard` per argument
        self.wildcards = [create_wildcard(a) for a in get_arg_hints(self.matchfunction)]

        # we match the wildcards against themselves to get an identity typevar mapping
        # TODO: Replace with just grabbing all typevars from arg types themselves
        typevars_in_args = match_values(
            tuple(self.wildcards), tuple(self.wildcards)
        ).keys()
        # Set the typevar args in scope so when functions are called here they are recorded properly
        with TypeVarScope(*typevars_in_args):
            # Call the function first to create a template with the wildcards
            result = self.matchfunction(*self.wildcards)
            self.results = (
                list(result)  # type: ignore
                if inspect.isgeneratorfunction(self.matchfunction)
                else [result]
            )

    def optimize(self, executor: Executor, strategy: Strategy) -> None:
        new_results: typing.List[R] = []

        for i, result in enumerate(self.results):
            template, expression_thunk = result
            # apply execution to all results that are not thunks
            if not isinstance(expression_thunk, types.FunctionType):
                self.results[i] = (template, executor(expression_thunk, strategy))

    def __call__(self, ref: ExpressionReference) -> typing.Iterable[Result]:
        expr = ref.expression
        with CaptureLogging() as logs:
            logger.debug("Rule.__call__ self=%s expr=%s", self, expr)
            for i, result in enumerate(self.results):
                template, expression_thunk = result
                try:
                    logger.debug("Trying to match against %s", template)
                    typevars, wildcards_to_nodes = match_expression(  # type: ignore
                        self.wildcards, template, expr
                    )
                except NoMatch:
                    logger.debug("Not a match")
                    continue
                logger.debug(
                    "Matched expr=%s typevars=%s", wildcards_to_nodes, typevars
                )
                # if the result is a function, we can't use substitution, so instead we re-call
                # with args and use that result
                if isinstance(expression_thunk, types.FunctionType):
                    args = [
                        wildcards_to_nodes.get(wildcard, wildcard)
                        for wildcard in self.wildcards
                    ]
                    with TypeVarScope(*typevars.keys()):
                        _, expression_thunk = (
                            list(self.matchfunction(*args))[i]
                            if inspect.isgeneratorfunction(self.matchfunction)
                            else self.matchfunction(*args)
                        )
                        # If it's a function, make sure we have real values instead of placeholders
                        # for any of the nodes that are placeholders for something more specific
                        # than a typevar, object, or any
                        if any(
                            isinstance(node, PlaceholderExpression)
                            and not is_vague_type(wildcard_inner_type(wildcard))
                            for wildcard, node in wildcards_to_nodes.items()
                        ):
                            continue
                        try:
                            result_expr: object = expression_thunk()
                        except NoMatch:
                            continue
                else:
                    result_expr = ReplaceValues(wildcards_to_nodes)(expression_thunk)
                with TypeVarScope(*typevars.keys()):
                    result_expr = ReplaceTypevarsExpression(typevars)(result_expr)
                logger.debug("Rule.__call__ res=%s", result_expr)
                ref.replace(result_expr)
                yield Result(
                    # if there is more than one possible match from this strategy, also put the index of the match
                    name=str(self) if len(self.results) == 1 else f"{self}[{i}]",
                    logs="\n".join(logs),
                )
                return


@dataclasses.dataclass
class ReplaceValues:
    mapping: typing.Mapping

    def __call__(self, expr):
        if expr in self.mapping:
            return self.mapping[expr]
        if not isinstance(expr, Expression):
            return expr
        result = expr._map(self)

        # if any of the args are create_iterated_placeholder
        # then remove those and replaced with arg expanded.
        new_args: typing.List = []
        for arg in result.args:
            if (
                isinstance(arg, Expression)
                and arg.function == create_iterated_placeholder
            ):
                inner_args = arg.args[0]
                assert isinstance(inner_args, tuple)
                for inner_arg in inner_args:
                    new_args.append(inner_arg)
            else:
                new_args.append(arg)
        result.args = new_args
        return result


@dataclasses.dataclass(frozen=True)
class ReplaceTypevarsExpression:
    """
    Make sure all functions have typevars attached to them, so when we call those functions
    the typevars will be replaced.

    Use a class instead of a function so we can partially apply it and have equality based on typevars 
    """

    typevars: TypeVarMapping

    def __call__(self, expression: object) -> object:
        """
        Replaces all typevars found in the classmethods of an expression.
        """
        typevars = self.typevars
        if isinstance(expression, Expression):
            return expression._map(
                fn=self,
                function_fn=lambda fn: replace_fn_typevars(fn, typevars),  # type: ignore
                type_fn=lambda tp: replace_typevars(typevars, tp),
            )
        return replace_fn_typevars(
            expression,
            typevars,
            ReplaceTypevarsExpression(typevars=HashableMapping(typevars)),
        )


def wildcard_inner_type(wildcard: object) -> typing.Type:
    """
    Return inner type for a wildcard
    """
    return typing_inspect.get_args(typing_inspect.get_generic_type(wildcard))[0]


def is_vague_type(t: typing.Type) -> bool:
    """
    Returns true if the type is a typevar, object or typing.
    """
    return typing_inspect.is_typevar(t) or t == object or t == typing.Any


def match_expression(
    wildcards: typing.List[Expression], template: object, expr: object
) -> typing.Tuple[TypeVarMapping, WildcardMapping]:
    """
    Returns a mapping of wildcards to the objects at that level, or None if it does not match.

    template: the expression with wildcards in it
    expr: the expression without wildcards to match against

    A wildcard can match either an expression or a value. If it matches two nodes, they must be equal.
    """
    logger.debug(
        "match_expression wildcards=%s template=%s expr=%s", wildcards, template, expr
    )
    if template in wildcards:
        logger.debug(
            "template is a wildcard, matching expr to template to get typevars"
        )
        # Match type of wildcard with type of expression
        try:
            res = (
                match_values(template, expr),
                UnhashableMapping(Item(typing.cast(Expression, template), expr)),
            )
            logger.debug("got wildcard mapping %s", res)
            return res
        except TypeError:
            logger.debug("could not match types")
            raise NoMatch

    if isinstance(expr, Expression):
        logger.debug("value is expression")
        if not isinstance(template, Expression):
            logger.debug("...but template isn't so no match")
            raise NoMatch
        # Any typevars in the template that are unbound should be matched with their
        # versions in the expr

        try:
            fn_type_mapping: TypeVarMapping = match_functions(
                template.function, expr.function
            )
        except TypeError:
            logger.debug("could not match functions")
            raise NoMatch
        logger.debug("matched functions to get typevar_apping=%s", fn_type_mapping)
        if set(expr.kwargs.keys()) != set(template.kwargs.keys()):
            logger.debug("No match because typevars not same keys")
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
            (template_iterated,) = iterated_args
            template_index_iterated = template.args.index(template_iterated)

            template_args = list(template.args)
            # Swap template iterated with inner wildcard
            (template_args[template_index_iterated],) = template_iterated.args

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
        logger.debug("Matched args and kwargs")
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

"""
Useful for to convert object to boxed types.
"""
from __future__ import annotations

import typing

from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .maybe import *
from .pair import *
from .strategies import *

__all__ = ["Converter", "convert_identity_rule", "convert_to_maybe"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


class Converter(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def convert(cls, value: object) -> Maybe[T]:
        """
        Converts a value to a certain type.
        """
        ...


@register_convert
@rule
def convert_identity_rule(value: T) -> R[Maybe[T]]:
    """
    When the value is an instance of the type being converted, we can convert it.
    """
    yield Converter[T].convert(value), Maybe.just(value)
    yield Converter[T].convert(Maybe.just(value)), Maybe.just(value)
    yield Converter[T].convert(Maybe[T].nothing()), Maybe[T].nothing()


@register_convert
@rule
def convert_to_maybe(x: object) -> R[Maybe[Maybe[T]]]:
    return (
        Converter[Maybe[T]].convert(x),
        lambda: Maybe.just(
            Maybe[T].nothing() if x is None else Converter[T].convert(x)
        ),
    )


@register_convert
@rule
def convert_to_pair(l: object, r: object) -> R[Maybe[Pair[T, U]]]:
    return (
        Converter[Pair[T, U]].convert(Pair.create(l, r)),
        Converter[T].convert(l) & Converter[U].convert(r),
    )


@expression
def lift_abstraction_maybe(a: Abstraction[T, Maybe[U]]) -> Maybe[Abstraction[T, U]]:
    """
    Deprecated: This is a bad idea.

    This would require some kinda of global match context. i.e. imagine matchign on the result,
    in the just case, then you have a fn you call on two args... One ends up resulting in true, the other false,
    then you need to know that whole match body was false, and to actually match on the nothing result.
    """
    ...


@register_core
@rule
def lift_abstraction_maybe_rule(v: T, b: U) -> R[Maybe[Abstraction[T, U]]]:
    # Need to hard code in cases, b/c we don't wanna lift unbound variable outside of abstraction
    yield (
        lift_abstraction_maybe(Abstraction.create(v, Maybe.just(b))),
        Maybe.just(Abstraction.create(v, b)),
    )
    yield (
        lift_abstraction_maybe(Abstraction.create(v, Maybe[U].nothing())),
        Maybe[Abstraction[T, U]].nothing(),
    )


@register_convert
@rule
def convert_to_abstraction(a: Abstraction[T, U]) -> R[Maybe[Abstraction[V, Maybe[X]]]]:
    """
    Converting from one abstraction to another means putting a convert on the input and the output.
    """

    return (
        Converter[Abstraction[V, Maybe[X]]].convert(a),
        lambda: Maybe.just(
            Abstraction[V, Maybe[X]].from_fn(
                lambda v: Converter[T]
                .convert(v)
                .flat_map(
                    Abstraction[T, Maybe[X]].from_fn(
                        lambda t: Converter[X].convert(a(t))
                    )
                )
            )
        ),
    )


@register_convert
@rule
def convert_fn_to_abstraction(
    a: typing.Callable[[T], U]
) -> R[Maybe[Abstraction[V, Maybe[X]]]]:
    return (
        Converter[Abstraction[V, Maybe[X]]].convert(a),
        lambda: Converter[Abstraction[V, Maybe[X]]].convert(Abstraction.from_fn(a)),
    )

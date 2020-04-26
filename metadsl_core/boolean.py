from __future__ import annotations

import typing

from metadsl import *

from metadsl_rewrite import *

from .abstraction import *
from .conversion import *
from .maybe import *
from .strategies import *

__all__ = ["Boolean"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class Boolean(Expression):
    # TODO: Remove this
    @expression
    @classmethod
    def create(cls, b: bool) -> Boolean:
        ...

    @expression
    def if_(self, true: T, false: T) -> T:
        ...

    @expression
    def and_(self, other: Boolean) -> Boolean:
        ...

    @expression
    def or_(self, other: Boolean) -> Boolean:
        ...

    @expression
    @classmethod
    def true(cls) -> Boolean:
        return Boolean.create(True)

    @expression
    @classmethod
    def false(cls) -> Boolean:
        return Boolean.create(False)


register_ds(default_rule(Boolean.true))
register_ds(default_rule(Boolean.false))


@register_ds  # type: ignore
@rule
def if_(b: bool, l: T, r: T) -> R[T]:
    return Boolean.create(b).if_(l, r), lambda: l if b else r


@register_ds  # type: ignore
@rule
def and_or(l: bool, r: bool) -> R[Boolean]:
    l_boolean = Boolean.create(l)
    r_boolean = Boolean.create(r)

    yield l_boolean.and_(r_boolean), lambda: Boolean.create(l and r)
    yield l_boolean.or_(r_boolean), lambda: Boolean.create(l or r)


@register_convert
@rule
def convert_bool(b: bool) -> R[Maybe[Boolean]]:
    """
    >>> execute(Converter[Boolean].convert(True), convert_bool) == Maybe.just(Boolean.create(True))
    True
    >>> list(convert_bool(ExpressionReference.from_expression(Converter[Boolean].convert("not bool"))))
    []
    """
    return Converter[Boolean].convert(b), Maybe.just(Boolean.create(b))


@register_core
@rule
def pull_if_above_maybe(
    b: Boolean,
    maybe_true: Maybe[T],
    maybe_false: Maybe[T],
    nothing: U,
    just: Abstraction[T, U],
):
    """
    Pull up if opreator around match... maybe could also pull this up generically on other operators?

    Do we want to pull if up always?
    """

    return (
        b.if_(maybe_true, maybe_false).match(nothing, just),
        b.if_(maybe_true.match(nothing, just), maybe_false.match(nothing, just)),
    )

from __future__ import annotations
import typing


from metadsl import *
from metadsl_core import *

from .injest import *
from .boxing import *

__all__ = ["BoolCompat", "If", "if_guess"]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class BoolCompat(Expression):
    """
    API should be work like Python's `bool` type.
    """

    @expression
    @classmethod
    def from_maybe_boolean(cls, i: Maybe[Boolean]) -> BoolCompat:
        ...

    @expression
    def and_(self, other: object) -> BoolCompat:
        ...

    @expression
    def or_(self, other: object) -> BoolCompat:
        ...


@guess_type.register
def guess_bool(b: bool):
    return BoolCompat, Boolean

@register_convert
@rule
def convert_to_boolean(i: Maybe[Boolean]) -> R[Maybe[Boolean]]:
    return Converter[Boolean].convert(BoolCompat.from_maybe_boolean(i)), i


@register
@rule
def box_boolean(b: Maybe[Boolean]) -> R[BoolCompat]:
    return Boxer[BoolCompat, Boolean].box(b), BoolCompat.from_maybe_boolean(b)


@register_convert
@rule
def and_if(maybe_l: Maybe[Boolean], r: object) -> R[BoolCompat]:
    maybe_r = Converter[Boolean].convert(r)
    maybe = maybe_l & maybe_r
    compat_l = BoolCompat.from_maybe_boolean(maybe_l)

    def create_result(m: typing.Callable[[Boolean, Boolean], Boolean]) -> BoolCompat:
        return BoolCompat.from_maybe_boolean(
            maybe.map(
                Abstraction[Pair[Boolean, Boolean], Boolean].from_fn(
                    lambda p: m(p.left, p.right)
                )
            )
        )

    yield (
        compat_l.and_(r),
        create_result(lambda l_bool, r_bool: l_bool.and_(r_bool)),
    )

    yield (
        compat_l.or_(r),
        create_result(lambda l_bool, r_bool: l_bool.or_(r_bool)),
    )


class If(Expression, typing.Generic[T, U]):
    """
    Create a new class for If so we can pass a typevar to it.
    """

    @expression
    @classmethod
    def if_(cls, cond: object, true: object, false: object) -> T:
        ...


def if_guess(cond: object, l: object, r: object) -> typing.Any:
    compat_tp, inner_tp = guess_first_type(l, r)
    return If[
        compat_tp, inner_tp  # type: ignore
    ].if_(
        cond, l, r
    )


@register  # type: ignore
@rule
def if_(cond: object, true: object, false: object) -> R[T]:
    return (
        If[T, U].if_(cond, true, false),
        Boxer[T, U].box(
            (
                Boxer[T, U].convert(cond)
                & (Boxer[T, U].convert(true) & Boxer[T, U].convert(false))
            ).map(
                Abstraction[Pair[Boolean, Pair[U, U]], U].from_fn(
                    lambda p: p.left.if_(*p.right.spread)
                )
            )
        ),
    )

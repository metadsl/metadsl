from __future__ import annotations
import typing


from metadsl import *
from metadsl_core import *
from metadsl_rewrite import *
from .injest import *
from .boxing import *

__all__ = ["BoolCompat"]

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

    def if_(self, l: object, r: object) -> object:
        compat_tp, inner_tp = guess_types(l, r)
        boxer = Boxer[compat_tp, inner_tp]  # type: ignore
        return boxer.box(self.if_maybe(boxer.convert(l), boxer.convert(r)))

    @expression
    def if_maybe(self, l: Maybe[T], r: Maybe[T]) -> Maybe[T]:
        ...


@guess_type.register(BoolCompat)
@guess_type.register(Boolean)
@guess_type.register(bool)
def guess_bool_compat(b: object):
    return BoolCompat, Boolean


@register_convert
@rule
def box_boolean(b: Maybe[Boolean]) -> R[BoolCompat]:
    return Boxer[BoolCompat, Boolean].box(b), BoolCompat.from_maybe_boolean(b)


@register_convert
@rule
def convert_bool_compat(b: Maybe[Boolean]) -> R[Maybe[Boolean]]:
    return Converter[Boolean].convert(BoolCompat.from_maybe_boolean(b)), b


@register_convert
@rule
def and_or(maybe_l: Maybe[Boolean], r: object) -> R[BoolCompat]:
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


@register_convert  # type: ignore
@rule
def if_maybes(cond: Maybe[Boolean], true: Maybe[T], false: Maybe[T]) -> R[Maybe[T]]:
    return (
        BoolCompat.from_maybe_boolean(cond).if_maybe(true, false),
        (cond & (true & false)).map(
            Abstraction[Pair[Boolean, Pair[T, T]], T].from_fn(
                lambda p: p.left.if_(*p.right.spread)
            )
        ),
    )

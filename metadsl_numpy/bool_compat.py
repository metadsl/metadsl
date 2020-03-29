from __future__ import annotations
import typing


from metadsl import *
from metadsl_core import *

from .injest import *

__all__ = ["BoolCompat", "BoolCompatIf", "if_bool"]

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
def guess_bool(b: bool) -> typing.Type[BoolCompat]:
    return BoolCompat


@register_convert
@rule
def convert_to_boolean(i: Maybe[Boolean]) -> R[Maybe[Boolean]]:
    return Converter[Boolean].convert(BoolCompat.from_maybe_boolean(i)), i


@register_convert
@rule
def convert_to_bool_compat(x: object) -> R[Maybe[BoolCompat]]:
    return (
        Converter[BoolCompat].convert(x),
        Maybe.just(BoolCompat.from_maybe_boolean(Converter[Boolean].convert(x))),
    )


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


class BoolCompatIf(Expression, typing.Generic[T]):
    """
    Create a new class for the if operation, so we can instatiate it with
    a constructor that takes a Maybe[object] and gives a U.

    Otherwise, if wouldn't work in maybe false use case
    """

    @expression
    @classmethod
    def create(cls, fn: Abstraction[Maybe[object], T]) -> BoolCompatIf[T]:
        ...

    @expression
    def __call__(self, cond: object, true: U, false: U) -> T:
        ...


@register  # type: ignore
@rule
def if_(fn: Abstraction[Maybe[object], U], cond: object, true: T, false: T) -> R[U]:
    return (
        BoolCompatIf.create(fn)(cond, true, false),
        fn(
            Converter[Boolean]
            .convert(cond)
            .map(Abstraction[Boolean, object].from_fn(lambda b: b.if_(true, false)))
        ),
    )


if_bool = BoolCompatIf.create(
    Abstraction[Maybe[object], BoolCompat].from_fn(
        lambda o: BoolCompat.from_maybe_boolean(Converter[Boolean].convert(o))
    )
)

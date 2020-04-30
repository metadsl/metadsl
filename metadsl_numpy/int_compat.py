from __future__ import annotations
import typing


from metadsl import *
from metadsl_core import *
from .bool_compat import *
from .injest import *
from .boxing import *
from metadsl_rewrite import *

__all__ = ["IntCompat"]


class IntCompat(Expression):
    """
    API should be work like Python's `int` type.
    """

    @expression
    @classmethod
    def from_maybe_integer(cls, i: Maybe[Integer]) -> IntCompat:
        ...

    # Numeric
    @expression
    def __add__(self, other: object) -> IntCompat:
        ...

    @expression
    def __sub__(self, other: object) -> IntCompat:
        ...

    @expression
    def __mul__(self, other: object) -> IntCompat:
        ...

    @expression
    def __floordiv__(self, other: object) -> IntCompat:
        ...

    @expression
    def __mod__(self, other: object) -> IntCompat:
        ...

    # Right numeric

    @expression
    def __radd__(self, other: object) -> IntCompat:
        ...

    @expression
    def __rsub__(self, other: object) -> IntCompat:
        ...

    @expression
    def __rmul__(self, other: object) -> IntCompat:
        ...

    @expression
    def __rfloordiv__(self, other: object) -> IntCompat:
        ...

    @expression
    def __rmod__(self, other: object) -> IntCompat:
        ...

    # Comparison
    @expression
    def eq(self, other: object) -> BoolCompat:
        ...

    @expression
    def __lt__(self, other: object) -> BoolCompat:
        ...

    @expression
    def __le__(self, other: object) -> BoolCompat:
        ...

    @expression
    def __gt__(self, other: object) -> BoolCompat:
        ...

    @expression
    def __ge__(self, other: object) -> BoolCompat:
        ...


@guess_type.register(IntCompat)
@guess_type.register(Integer)
@guess_type.register(int)
def guess_int(i: object):
    return IntCompat, Integer


@register_convert
@rule
def convert_to_integer(i: Maybe[Integer]) -> R[Maybe[Integer]]:
    return Converter[Integer].convert(IntCompat.from_maybe_integer(i)), i


@register_convert
@rule
def box_int_compat(x: Maybe[Integer]) -> R[IntCompat]:
    return (
        Boxer[IntCompat, Integer].box(x),
        IntCompat.from_maybe_integer(x),
    )


@register_convert
@rule
def int_compat_operators(maybe_l: Maybe[Integer], r: object) -> R[IntCompat]:
    maybe_r = Converter[Integer].convert(r)
    maybe = maybe_l & maybe_r
    compat_l = IntCompat.from_maybe_integer(maybe_l)

    def create_int_result(
        m: typing.Callable[[Integer, Integer], Integer]
    ) -> typing.Callable[[], IntCompat]:
        return lambda: IntCompat.from_maybe_integer(
            maybe.map(
                Abstraction[Pair[Integer, Integer], Integer].from_fn(
                    lambda p: m(p.left, p.right)
                )
            )
        )

    def create_bool_result(
        m: typing.Callable[[Integer, Integer], Boolean]
    ) -> typing.Callable[[], BoolCompat]:
        return lambda: BoolCompat.from_maybe_boolean(
            maybe.map(
                Abstraction[Pair[Integer, Integer], Boolean].from_fn(
                    lambda p: m(p.left, p.right)
                )
            )
        )

    # numeric
    yield (
        compat_l + r,
        create_int_result(lambda l_int, r_int: l_int + r_int),
    )
    yield (
        compat_l - r,
        create_int_result(lambda l_int, r_int: l_int - r_int),
    )
    yield (
        compat_l * r,
        create_int_result(lambda l_int, r_int: l_int * r_int),
    )
    yield (
        compat_l // r,
        create_int_result(lambda l_int, r_int: l_int // r_int),
    )
    yield (
        compat_l % r,
        create_int_result(lambda l_int, r_int: l_int % r_int),
    )

    # right numeric
    yield (
        r + compat_l,
        create_int_result(lambda l_int, r_int: r_int + l_int),
    )
    yield (
        r - compat_l,
        create_int_result(lambda l_int, r_int: r_int - l_int),
    )
    yield (
        r * compat_l,
        create_int_result(lambda l_int, r_int: r_int * l_int),
    )
    yield (
        r // compat_l,
        create_int_result(lambda l_int, r_int: r_int // l_int),
    )
    yield (
        r % compat_l,
        create_int_result(lambda l_int, r_int: r_int % l_int),
    )

    # comparison
    yield (
        compat_l.eq(r),
        create_bool_result(lambda l_int, r_int: l_int.eq(r_int)),
    )
    yield (
        compat_l < r,
        create_bool_result(lambda l_int, r_int: l_int < r_int),
    )
    yield (
        compat_l <= r,
        create_bool_result(lambda l_int, r_int: l_int <= r_int),
    )
    yield (
        compat_l > r,
        create_bool_result(lambda l_int, r_int: l_int > r_int),
    )
    yield (
        compat_l >= r,
        create_bool_result(lambda l_int, r_int: l_int >= r_int),
    )

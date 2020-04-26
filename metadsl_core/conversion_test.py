import pytest
from metadsl import *
from metadsl_rewrite import *

from .abstraction import *
from .conversion import *
from .maybe import *
from .strategies import *


class TestConvertIdentity:
    def test_matches_type(self):
        assert execute(Converter[int].convert(1)) == Maybe.just(1)

    def test_doesnt_match_type(self):
        assert not list(
            convert_identity_rule(
                ExpressionReference.from_expression(Converter[str].convert(1))
            )
        )

    def test_matches_convert(self):
        assert execute(Converter[int].convert(Maybe.just(1))) == Maybe.just(1)
        assert (
            execute(Converter[int].convert(Maybe[int].nothing()))
            == Maybe[int].nothing()
        )


class TestConvertToMaybe:
    def test_just(self):
        assert execute(Converter[Maybe[int]].convert(1)) == Maybe.just(Maybe.just(1))

    def test_nothing(self):
        assert execute(Converter[Maybe[int]].convert(None)) == Maybe.just(
            Maybe[int].nothing()
        )


class T(Expression):
    ...


class U(Expression):
    ...


class V(Expression):
    ...


class X(Expression):
    ...


@expression
def t_to_u(t: T) -> U:
    ...


@expression
def v() -> V:
    ...


@expression
def v_to_t(v: V) -> T:
    ...


@expression
def u_to_x(u: U) -> X:
    ...


@rule
def convert_v_to_t_just(v: V) -> R[Maybe[T]]:
    return Converter[T].convert(v), Maybe.just(v_to_t(v))


@rule
def convert_v_to_t_nothing(v: V) -> R[Maybe[T]]:
    return Converter[T].convert(v), Maybe[T].nothing()


@rule
def convert_u_to_x_just(u: U) -> R[Maybe[X]]:
    return Converter[X].convert(u), Maybe.just(u_to_x(u))


@rule
def convert_u_to_x_nothing(u: U) -> R[Maybe[X]]:
    return Converter[X].convert(u), Maybe[X].nothing()


class TestConvertToAbstraction:
    @pytest.mark.parametrize(
        "u_to_x_rule",
        [convert_v_to_t_just, convert_u_to_x_nothing],
        ids=["just", "nothing"],
    )
    @pytest.mark.parametrize(
        "v_to_t_rule",
        [convert_v_to_t_just, convert_v_to_t_nothing],
        ids=["just", "nothing"],
    )
    def test_from_abstraction(self, u_to_x_rule, v_to_t_rule) -> None:
        """
        Test converting from a function to an abstraction
        """

        def fn(t: T) -> U:
            return t_to_u(t)

        converted_a = Converter[Abstraction[V, Maybe[X]]].convert(fn)
        called_with_v: Maybe[X] = converted_a.flat_map(
            Abstraction[Abstraction[V, Maybe[X]], Maybe[X]].from_fn(lambda a: a(v()))
        )

        desired_result: Maybe[X] = (
            Converter[T]
            .convert(v())
            .flat_map(
                Abstraction[T, Maybe[X]].from_fn(
                    lambda t: Converter[X].convert(t_to_u(t))
                )
            )
        )
        with register.tmp(v_to_t_rule, u_to_x_rule):
            assert execute(called_with_v) == execute(desired_result)

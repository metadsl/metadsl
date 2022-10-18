from __future__ import annotations

import typing

import pytest
import typing_inspect

from .expressions import *

T = typing.TypeVar("T")


@expression
def fn(a: T, b: T) -> T:
    ...


@expression
def value_fn(a: int) -> Expression:
    ...


class Subclass(Expression):
    pass


@expression
def subclass_fn(a: int) -> Subclass:
    ...


def test_expression_subclass() -> None:
    assert isinstance(subclass_fn(1), Subclass)


class Generic(Expression, typing.Generic[T]):
    def get_inner_type(self) -> typing.Type[T]:
        return typing_inspect.get_args(typing_inspect.get_generic_type(self))[0]

    @expression
    def get(self) -> T:
        ...

    @expression
    @classmethod
    def create(cls) -> Generic[T]:
        ...


@expression
def instance_arg_fn(a: int) -> Generic[int]:
    ...


def test_expression_subclass_generic() -> None:
    assert instance_arg_fn(10).get_inner_type() == int


@expression
def mutable_fn(a: typing.List) -> Expression:
    ...


class SubclassWithMethod(Expression):
    @expression
    def __add__(self, other: SubclassWithMethod) -> SubclassWithMethod:
        ...


def test_classmethod():
    c = Generic[Subclass].create()
    assert isinstance(c.get(), Subclass)


@expression
def create_method_subclass(i: int) -> SubclassWithMethod:
    ...


@expression
def variadic(*args: int) -> Expression:
    ...


def test_variadic():
    assert variadic(1, 2).args == [1, 2]


@expression
def create_variadic_ints() -> typing.Sequence[int]:
    ...


def test_iterated():
    assert variadic(1, 2, *create_variadic_ints(), 3, 4) == Expression(
        variadic,
        [
            1,
            2,
            IteratedPlaceholder[int](
                create_iterated_placeholder,
                [
                    PlaceholderExpression[typing.Sequence[int]](
                        create_variadic_ints, [], {}
                    )
                ],
                {},
            ),
            3,
            4,
        ],
        {},
    )


TEST_EXPRESSIONS: typing.Iterable[object] = [
    value_fn(123),
    fn(value_fn(10), value_fn(11)),
    fn(subclass_fn(1), subclass_fn(2)),
    instance_arg_fn(10),
    create_method_subclass(10) + create_method_subclass(10),
    mutable_fn([1, 2, 3]),  # mutable value that doesn't have hash
    variadic(1, 2, 3),
    Generic[int].create(),
    Generic[Generic[int]].create(),
]


@pytest.mark.parametrize("instance", TEST_EXPRESSIONS)
def test_clone_expression(instance) -> None:
    """
    You should be able to decompose any instances into it's type and expression and recompose it.
    """
    assert clone_expression(instance) == instance


U = typing.TypeVar("U")


def test_clone_expression_generic():
    assert clone_expression(Generic[T].create()) == Generic[T].create()
    assert clone_expression(Generic[U].create()) == Generic[U].create()


class A(Expression, wrap_methods=True):
    @classmethod
    def create(cls) -> A:
        ...

    def method(self) -> A:
        ...

    @property
    def prop(self) -> A:
        ...


def test_wrap_method() -> None:
    assert A.create() == A(A.create, [], {})
    assert A.create().method() == A(A.method, [A(A.create, [], {})], {})
    assert A.create().prop == A(A.prop, [A(A.create, [], {})], {})

from __future__ import annotations

import typing

import pytest

from .typing_tools import *

T = typing.TypeVar("T")


def extract_return_type(fn, args, kwargs, return_type):
    return return_type


def i(fn):
    return infer(fn, extract_return_type)


def test_simple():
    @i
    def _simple_return() -> int:
        ...

    assert _simple_return() == int


def test_generic():
    @i
    def _generic_return(arg: T) -> T:
        ...

    assert _generic_return(123.0) == float


class _GenericClass(GenericCheck, typing.Generic[T]):
    ...


def test_generic_class_return():
    @i
    def create(t: T) -> _GenericClass[T]:
        ...

    assert create(123) == _GenericClass[int]


class _GenericClassMethod(GenericCheck, typing.Generic[T]):
    @i
    def method(self) -> T:
        ...


def test_generic_class_arg():

    assert _GenericClassMethod[int]().method() == int
    assert (
        _GenericClassMethod[_GenericClassMethod[int]]().method()
        == _GenericClassMethod[int]
    )


class _GenericClassClassMethod(GenericCheck, typing.Generic[T]):
    @i
    @classmethod
    def create(cls) -> _GenericClassClassMethod[T]:
        ...


def test_generic_classmethood():

    assert _GenericClassClassMethod[int].create() == _GenericClassClassMethod[int]
    assert _GenericClassClassMethod[float].create() == _GenericClassClassMethod[float]
    assert _GenericClassClassMethod[int].create() != _GenericClassClassMethod


class _NonGenericClass:
    @i
    def method(self) -> int:
        ...


def test_non_generic_method():

    assert _NonGenericClass().method() == int


class _NonGenericClassClassMethod(GenericCheck):
    @i
    @classmethod
    def create(cls, i: int) -> int:
        ...


def test_non_generic_classmethod():

    assert _NonGenericClassClassMethod.create(123) == int


def test_union_arg():
    @i
    def _union_arg(a: typing.Union[int, str]) -> int:
        ...

    assert _union_arg(123) == int
    assert _union_arg("sdf") == int
    with pytest.raises(TypeError):
        _union_arg([1, 2, 3])


def test_variable_args():
    @i
    def many_args(*x: T) -> T:
        ...

    assert many_args(1) == int
    with pytest.raises(TypeError):
        many_args(1, "hj")


def test_variable_args_empty():
    @i
    def many_args(*x: int) -> int:
        ...

    assert many_args() == int


def test_keyword_args():
    @i
    def many_args(a: int, b: T) -> T:
        ...

    assert many_args(b="df", a=123) == str


def test_keyword_default():
    @i
    def default_kwarg(b: T = 10) -> T:  # type: ignore
        ...

    assert default_kwarg() == int
    assert default_kwarg(b="df") == str

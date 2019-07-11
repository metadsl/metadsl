from __future__ import annotations

import typing

import pytest

from .typing_tools import *

T = typing.TypeVar("T")


def i(fn):
    return infer(fn, lambda *args: args)


def test_simple():
    @i
    def _simple_return() -> int:
        ...

    assert _simple_return() == (_simple_return, (), {}, int)


def test_generic():
    @i
    def _generic_return(arg: T) -> T:
        ...

    assert _generic_return(123.0) == (_generic_return, (123.0,), {}, float)


class _GenericClassMethod(GenericCheck, typing.Generic[T]):
    @i
    def method(self) -> T:
        ...


def test_generic_class_arg():
    c = _GenericClassMethod[int]()
    assert c.method() == (_GenericClassMethod[int].method, (c,), {}, int)


def test_generic_arg_call_on_class():
    c = _GenericClassMethod[int]()
    assert _GenericClassMethod.method(c) == (_GenericClassMethod.method, (c,), {}, int)
    assert _GenericClassMethod[int].method(c) == (
        _GenericClassMethod[int].method,
        (c,),
        {},
        int,
    )

    c2 = _GenericClassMethod[_GenericClassMethod[int]]()
    assert c2.method() == (
        _GenericClassMethod[_GenericClassMethod[int]].method,
        (c2,),
        {},
        _GenericClassMethod[int],
    )


def test_generic_arg_call_on_class_generic_class():
    c: _GenericClassMethod = _GenericClassMethod()
    assert _GenericClassMethod[int].method(c) == (
        _GenericClassMethod[int].method,
        (c,),
        {},
        int,
    )


class _GenericClassCreate(GenericCheck, typing.Generic[T]):
    @i
    @classmethod
    def create(cls) -> T:
        ...

    @i
    @classmethod
    def create_item(cls, item: T) -> T:
        ...


def test_create():
    assert _GenericClassCreate[int].create() == (
        _GenericClassCreate[int].create,
        (),
        {},
        int,
    )

    assert _GenericClassCreate[_GenericClassMethod[int]].create() == (
        _GenericClassCreate[_GenericClassMethod[int]].create,
        (),
        {},
        _GenericClassMethod[int],
    )


def test_create_type_from_arg():

    assert _GenericClassCreate.create_item(123) == (
        _GenericClassCreate.create_item,
        (123,),
        {},
        int,
    )

    assert _GenericClassCreate[int].create_item(123) == (
        _GenericClassCreate[int].create_item,
        (123,),
        {},
        int,
    )


class _NonGenericClass:
    @i
    def method(self) -> int:
        ...


def test_non_generic_method():

    c = _NonGenericClass()
    assert c.method() == (_NonGenericClass.method, (c,), {}, int)
    assert _NonGenericClass.method(c) == (_NonGenericClass.method, (c,), {}, int)


def test_variable_args():
    @i
    def many_args(*x: T) -> T:
        ...

    assert many_args(1) == (many_args, (1,), {}, int)
    with pytest.raises(TypeError):
        many_args(1, "hj")


def test_variable_args_empty():
    @i
    def many_args(*x: int) -> int:
        ...

    assert many_args() == (many_args, (), {}, int)


def test_keyword_args():
    @i
    def many_args(a: int, b: T) -> T:
        ...

    assert many_args(b="df", a=123) == (many_args, (123, "df"), {}, str)


def test_keyword_default():
    @i
    def default_kwarg(b: T = 10) -> T:  # type: ignore
        ...

    assert default_kwarg() == (default_kwarg, (10,), {}, int)
    assert default_kwarg(b="df") == (default_kwarg, ("df",), {}, str)


def test_tuple_for_sequence():
    @i
    def fn(xs: typing.Sequence[T]) -> T:  # type: ignore
        ...

    assert fn((1, 2)) == (fn, ((1, 2),), {}, int)


def test_fn_args():
    @i
    def fn(f: typing.Callable) -> int:
        ...

    f = lambda i: 10
    assert fn(f) == (fn, (f,), {}, int)


def test_fn_args_generic():
    def f(i: int) -> str:
        ...

    assert _GenericClassCreate[typing.Callable[[int], str]].create_item(f) == (
        _GenericClassCreate[typing.Callable[[int], str]].create_item,
        (f,),
        {},
        typing.Callable[[int], str],
    )


U = typing.TypeVar("U")


class Both(typing.Generic[T, U]):
    ...


class ConflictingTypevars(typing.Generic[T]):
    @i
    def __add__(self, other: ConflictingTypevars[U]) -> ConflictingTypevars[Both[T, U]]:
        ...


def test_generic_class_conflicting_typevars():
    """
    We should make sure that if you use a typevar in a generic class, it gets resolved locally.
    """
    l = ConflictingTypevars[int]()
    r = ConflictingTypevars[str]()
    assert l + r == (
        ConflictingTypevars[int].__add__,
        (l, r),
        {},
        ConflictingTypevars[Both[int, str]],
    )


V = typing.TypeVar("V")


class ConflictingTypevarsMultiple(typing.Generic[T, U]):
    @i
    def __add__(
        self, other: ConflictingTypevarsMultiple[U, V]
    ) -> ConflictingTypevarsMultiple[T, V]:
        ...


def test_generic_class_conflicting_multiple_typevars():
    l = ConflictingTypevarsMultiple[int, str]()
    r = ConflictingTypevarsMultiple[str, float]()
    assert l + r == (
        ConflictingTypevarsMultiple[int, str].__add__,
        (l, r),
        {},
        ConflictingTypevarsMultiple[int, float],
    )


class C(typing.Generic[T]):
    @i
    def __add__(self, other: T) -> T:
        ...

    @i
    @classmethod
    def create(cls, arg: T) -> C[T]:
        ...


class TestGetType:
    def test_bound_infer_method(self):

        assert get_type(C[int]().__add__) == typing.Callable[[int], int]

    def test_bound_infer_method_on_class(self):

        assert get_type(C[int].__add__) == typing.Callable[[C[int], int], int]

    def test_bound_infer_classmethod(self):

        assert get_type(C[int].create) == typing.Callable[[int], C[int]]

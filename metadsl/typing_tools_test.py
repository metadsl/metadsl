import typing

import pytest

from .typing_tools import *

T = typing.TypeVar("T")


def _simple_return() -> int:
    ...


def _generic_return(arg: T) -> T:
    ...


class _GenericClass(typing.Generic[T]):
    def method(self) -> T:
        ...


class _NonGenericClass:
    def method(self) -> int:
        ...


def _generic_class_arg(arg: _GenericClass[T]) -> T:
    ...


def _generic_class_return(arg: T) -> _GenericClass[T]:
    ...


def _union_arg(a: typing.Union[int, _GenericClass[int]]) -> int:
    ...


class TestInferReturnType:
    def test_simple(self):
        assert infer_return_type(_simple_return) == int

    def test_generic(self):
        assert infer_return_type(_generic_return, float) == float
        assert infer_return_type(_generic_return, typing.List[int]) == typing.List[int]

    def test_generic_class_arg(self):
        assert infer_return_type(_generic_class_arg, _GenericClass[int]) == int
        assert (
            infer_return_type(_generic_class_arg, _GenericClass[_GenericClass[bool]])
            == _GenericClass[bool]
        )

    def test_generic_class_return(self):
        assert infer_return_type(_generic_class_return, int) == _GenericClass[int]
        assert (
            infer_return_type(_generic_class_return, _GenericClass[bool])
            == _GenericClass[_GenericClass[bool]]
        )

    def test_generic_class_method(self):
        assert infer_return_type(_GenericClass.method, _GenericClass[bool]) == bool

    def test_non_generic_class_method(self):
        assert infer_return_type(_NonGenericClass.method, _NonGenericClass) == int

    def test_union_arg_left(self):
        assert infer_return_type(_union_arg, int) == int

    def test_union_arg_right(self):
        assert infer_return_type(_union_arg, _GenericClass[int]) == int

    def test_union_arg_neither(self):
        with pytest.raises(TypeError):
            infer_return_type(_union_arg, float)
        with pytest.raises(TypeError):
            infer_return_type(_union_arg, _GenericClass[float])

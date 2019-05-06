import typing

from .typing_tools import *

T = typing.TypeVar("T")


def _simple_return() -> int:
    ...


def _generic_return(arg: T) -> T:
    ...


class _GenericClass(typing.Generic[T]):
    ...


def _generic_class_arg(arg: _GenericClass[T]) -> T:
    ...


def _generic_class_return(arg: T) -> _GenericClass[T]:
    ...

class TestInferReturnType:
    def test_simple(self):
        assert infer_return_type(_simple_return) == int

    def test_generic(self):
        assert infer_return_type(_generic_return, float) == float
        assert infer_return_type(_generic_return, typing.List[int]) == typing.List[int]

    def test_generic_class_arg(self):
        assert infer_return_type(_generic_class_arg, _GenericClass[int]) == int
        assert infer_return_type(_generic_class_arg, _GenericClass[_GenericClass[bool]]) == _GenericClass[bool]

    def test_generic_class_return(self):
        assert infer_return_type(_generic_class_return, int) == _GenericClass[int]
        assert infer_return_type(_generic_class_return, _GenericClass[bool]) == _GenericClass[_GenericClass[bool]]

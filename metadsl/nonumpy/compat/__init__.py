"""

No Numpy is a replica of the NumPy API that can be used without requiring NumPy.

You should be able to import from `metadsl.nonumpy.compat` just as you would from `numpy` and use all
the functions and objects you are accustomed to.

What will it actually do? Well not much. It will just build up an expression tree of the NumPy expression you have written.

It also comes included with some transformations of those expression trees you can use. It's a good building block if you are writing a NumPy-like API.

Things it does not preserve:

1. Primitive Python operations like `__str__` and `type`
2. Control flow operations like `if` and `for`
3. The C API
4. Mutation operations (like setting a slice)

It should be just as accepting as the default NumPy API in the type of objects it takes. 
"""
import typing

from metadsl.expressions import *
import metadsl.nonumpy.pure as np_pure
import metadsl.python.compat as py_compat
import metadsl.python.compat as py_pure

__all__ = [
    "array",
    "arange",
    "zeros",
    "ones",
    "asarray",
    "sqrt",
    "sum",
    "abs",
    "mean",
    "log",
]

T = typing.TypeVar("T", bound=Instance)
U = typing.TypeVar("U", bound=Instance)


class NDArray(Instance):
    @classmethod
    def from_value(cls, value: typing.Any) -> "NDArray":
        if isinstance(value, NDArray):
            return value
        if isinstance(value, np_pure.NDArray):
            return cls.from_pure(value)
        # TODO: check if valid numpy array type
        return cls(value)

    @classmethod
    def from_pure(cls, p: np_pure.NDArray) -> "NDArray":
        return cls(p.__value__)

    @property
    def pure(self) -> np_pure.NDArray:
        return np_pure.NDArray(self.__value__)

    @property
    def shape(self) -> py_compat.TupleOfIntegers:
        return py_compat.TupleOfIntegers.from_pure(self.pure.shape)

    def __add__(self, other) -> "NDArray":
        return self.from_pure(self.pure + self.from_value(other).pure)

    def __mul__(self, other) -> "NDArray":
        return self.from_pure(self.pure * self.from_value(other).pure)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs) -> "NDArray":
        return self.from_pure(
            np_pure.NDArray.__array_ufunc__(
                UFunc.from_value(ufunc).pure,
                UFuncMethod.from_value(method).pure,
                UFuncKwargs.from_value(kwargs).pure,
                *(NDArray.from_value(input).pure for input in inputs)
            )
        )


class UFunc(Instance):
    @classmethod
    def from_value(cls, value: typing.Any) -> "UFunc":
        if isinstance(value, UFunc):
            return value
        if isinstance(value, np_pure.UFunc):
            return cls.from_pure(value)
        return cls(value)

    @classmethod
    def from_pure(cls, p: np_pure.UFunc) -> "UFunc":
        return cls(p.__value__)

    @property
    def pure(self) -> np_pure.UFunc:
        return np_pure.UFunc(self.__value__)


class UFuncKwargs(Instance):
    @classmethod
    def from_value(cls, value: typing.Any) -> "UFuncKwargs":
        if isinstance(value, UFuncKwargs):
            return value
        if isinstance(value, np_pure.UFuncKwargs):
            return cls.from_pure(value)
        if isinstance(value, dict):
            return cls(tuple(value.items()))
        raise TypeError

    @classmethod
    def from_pure(cls, p: np_pure.UFuncKwargs) -> "UFuncKwargs":
        return cls(p.__value__)

    @property
    def pure(self) -> np_pure.UFuncKwargs:
        return np_pure.UFuncKwargs(self.__value__)


class UFuncMethod(Instance):
    @classmethod
    def from_value(cls, value: typing.Any) -> "UFuncMethod":
        if isinstance(value, UFuncMethod):
            return value
        if isinstance(value, np_pure.UFuncMethod):
            return cls.from_pure(value)
        return cls(value)

    @classmethod
    def from_pure(cls, p: np_pure.UFuncMethod) -> "UFuncMethod":
        return cls(p.__value__)

    @property
    def pure(self) -> np_pure.UFuncMethod:
        return np_pure.UFuncMethod(self.__value__)


def array(object, dtype=None, copy=True, order=None, subok=None, ndmin=None) -> NDArray:
    return NDArray.from_pure(
        np_pure.array(  # type: ignore
            NDArray.from_value(object).pure,
            py_compat.Optional.from_value(instance_type(np_pure.DType), dtype).pure,
            py_compat.Boolean.from_value(copy).pure,
            py_compat.Optional.from_value(
                instance_type(np_pure.ArrayOrder), order
            ).pure,
            py_compat.Optional.from_value(instance_type(py_pure.Boolean), subok).pure,
            py_compat.Optional.from_value(instance_type(py_pure.Integer), ndmin).pure,
        )
    )


# If arange is called with one positional argument, it is the stop, and you cannot set the start with a kward
@typing.overload
def arange(stop, *, step=None, dtype=None) -> NDArray:
    ...


# If arange is called with two positional arguments, the first is stop, and the second is start
@typing.overload
def arange(start, stop, step=None, dtype=None) -> NDArray:
    ...


def arange(*args, **kwargs) -> NDArray:
    start: typing.Any
    if len(args) == 1:
        stop, = args
        start = None
        assert kwargs.keys() < {"step", "dtype"}
        step, dtype = kwargs.get("step"), kwargs.get("dtype")
    elif len(args) == 2:
        start, stop = args
        assert kwargs.keys() < {"step", "dtype"}
        step, dtype = kwargs.get("step"), kwargs.get("dtype")
    elif len(args) == 3:
        start, stop, step = args
        assert kwargs.keys() < {"dtype"}
        dtype = kwargs.get("dtype")
    elif len(args) == 4:
        start, stop, step, dtype = args
        assert not kwargs.keys()
    else:
        raise RuntimeError("Cannot pass more than 4 arguments to `arange`")
    return NDArray.from_pure(
        np_pure.arange(  # type: ignore
            py_compat.Optional.from_value(instance_type(py_pure.Number), start).pure,
            py_compat.Number.from_value(stop).pure,
            py_compat.Optional.from_value(instance_type(py_pure.Number), step).pure,
            py_compat.Optional.from_value(instance_type(np_pure.DType), dtype).pure,
        )
    )

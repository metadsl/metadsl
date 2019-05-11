"""

This is a replica of the NumPy API that can be used without requiring NumPy.

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

from __future__ import annotations

import typing

from metadsl import *
import metadsl.numpy.pure as np_pure
import metadsl.python.compat as py_compat

__all__ = ["arange", "NDArray"]

T = typing.TypeVar("T")


@wrap(np_pure.arange)
def arange(start, stop, step, dtype) -> NDArray:
    ...


class NDArray(Wrap[np_pure.NDArray]):
    @wrap(np_pure.NDArray.shape)
    def shape(self) -> py_compat.IntegerTuple:
        ...

    @wrap(np_pure.NDArray.__add__)
    def __add__(self, other: object) -> NDArray:
        ...

    @wrap(np_pure.NDArray.__mul__)
    def __mul__(self, other: object) -> NDArray:
        ...

    @wrap(np_pure.NDArray.__getitem__)
    def __getitem__(self, idxs: object) -> NDArray:
        ...

    # def __gt__(self, other) -> "NDArray":
    #     return self.from_pure(
    #         self.pure > create_instance(instance_type(np_pure.NDArray), other)
    #     )

    # def __ge__(self, other) -> "NDArray":
    #     return self.from_pure(
    #         self.pure >= create_instance(instance_type(np_pure.NDArray), other)
    #     )

    # def __lt__(self, other) -> "NDArray":
    #     return self.from_pure(
    #         self.pure < create_instance(instance_type(np_pure.NDArray), other)
    #     )

    # def __le__(self, other) -> "NDArray":
    #     return self.from_pure(
    #         self.pure <= create_instance(instance_type(np_pure.NDArray), other)
    #     )

    # def __array_ufunc__(self, ufunc, method, *inputs, **kwargs) -> "NDArray":
    #     return self.from_pure(
    #         np_pure.NDArray.__array_ufunc__(
    #             create_instance(instance_type(np_pure.UFunc), ufunc),
    #             create_instance(instance_type(np_pure.UFuncMethod), method),
    #             create_instance(instance_type(np_pure.UFuncKwargs), kwargs),
    #             *(
    #                 create_instance(instance_type(np_pure.NDArray), input)
    #                 for input in inputs
    #             )
    #         )
    #     )

    # def __array_function__(self, func, types, args, kwargs) -> "NDArray":
    #     return self.from_pure(
    #         np_pure.NDArray.__array_function__(
    #             create_instance(instance_type(np_pure.NumPyFunction), func),
    #             create_instance(
    #                 instance_type(py_pure.Tuple, instance_type(Instance)), args
    #             ),
    #             create_instance(instance_type(Instance), kwargs),
    #         )
    #     )


# class UFunc(Instance):
#     @classmethod
#     def from_pure(cls, p: np_pure.UFunc) -> "UFunc":
#         return cls(p.__value__)

#     @property
#     def pure(self) -> np_pure.UFunc:
#         return np_pure.UFunc(self.__value__)


# class UFuncKwargs(Instance):
#     @classmethod
#     def from_pure(cls, p: np_pure.UFuncKwargs) -> "UFuncKwargs":
#         return cls(p.__value__)

#     @property
#     def pure(self) -> np_pure.UFuncKwargs:
#         return np_pure.UFuncKwargs(self.__value__)


# class UFuncMethod(Instance):
#     @classmethod
#     def from_pure(cls, p: np_pure.UFuncMethod) -> "UFuncMethod":
#         return cls(p.__value__)

#     @property
#     def pure(self) -> np_pure.UFuncMethod:
#         return np_pure.UFuncMethod(self.__value__)


# def array(object, dtype=None, copy=True, order=None, subok=None, ndmin=None) -> NDArray:
#     return NDArray.from_pure(
#         np_pure.array(
#             create_instance(instance_type(np_pure.NDArray), object),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(np_pure.DType)), dtype
#             ),
#             create_instance(instance_type(py_pure.Boolean), copy),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(np_pure.ArrayOrder)),
#                 order,
#             ),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(py_pure.Boolean)), subok
#             ),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(py_pure.Integer)), ndmin
#             ),
#         )
#     )


# # If arange is called with one positional argument, it is the stop, and you cannot set the start with a kward
# @typing.overload
# def arange(stop, *, step=None, dtype=None) -> NDArray:
#     ...


# # If arange is called with two positional arguments, the first is stop, and the second is start
# @typing.overload
# def arange(start, stop, step=None, dtype=None) -> NDArray:
#     ...


# def arange(*args, **kwargs) -> NDArray:
#     start: typing.Any
#     if len(args) == 1:
#         stop, = args
#         start = None
#         assert kwargs.keys() < {"step", "dtype"}
#         step, dtype = kwargs.get("step"), kwargs.get("dtype")
#     elif len(args) == 2:
#         start, stop = args
#         assert kwargs.keys() < {"step", "dtype"}
#         step, dtype = kwargs.get("step"), kwargs.get("dtype")
#     elif len(args) == 3:
#         start, stop, step = args
#         assert kwargs.keys() < {"dtype"}
#         dtype = kwargs.get("dtype")
#     elif len(args) == 4:
#         start, stop, step, dtype = args
#         assert not kwargs.keys()
#     else:
#         raise RuntimeError("Cannot pass more than 4 arguments to `arange`")
#     return NDArray.from_pure(
#         np_pure.arange(
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(py_pure.Number)), start
#             ),
#             create_instance(instance_type(py_pure.Number), stop),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(py_pure.Number)), step
#             ),
#             create_instance(
#                 instance_type(py_pure.Optional, instance_type(np_pure.DType)), dtype
#             ),
#         )
#     )

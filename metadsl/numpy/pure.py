from __future__ import annotations


from metadsl import *
from metadsl.python.pure import *

__all__ = [
    "NDArray",
    "DType",
    "ArrayOrder",
    "Optional",
    "Number",
    "array",
    "arange",
    "UFunc",
    "UFuncKwargs",
    "UFuncMethod",
]

class NDArray(Expression):
    @property  # type: ignore
    @expression
    def shape(self) -> Tuple[Integer]:
        ...

    @expression
    def __add__(self, other: NDArray) -> NDArray:
        ...

    @expression
    def __mul__(self, other: NDArray) -> NDArray:
        ...

    @expression
    def __getitem__(self, idxs: Union[Integer, Tuple[Integer]]) -> NDArray:
        ...

    # @staticmethod
    # @expression
    # def __array_ufunc__(
    #     ufunc: "UFunc", method: "UFuncMethod", kwargs: "UFuncKwargs", *inputs: NDArray
    # ) -> NDArray:
    #     ...

    # @staticmethod
    # @expression
    # def __array_function__(
    #     func: NumPyFunction, args: Tuple[Instance], kwargs: Instance
    # ) -> NDArray:
    #     pass


# class NumPyFunction(Instance):
#     pass


class DType(Expression):
    pass


# class UFunc(Instance):
#     pass


# class UFuncKwargs(Instance):
#     pass


# class UFuncMethod(Instance):
#     """
#     https://docs.scipy.org/doc/numpy-1.13.0/neps/ufunc-overrides.html#proposed-interface

#     method is a string indicating how the Ufunc was called, either "__call__" to indicate it was called directly, or one of its methods: "reduce", "accumulate", "reduceat", "outer", or "at".
#     """

#     @call(lambda self, k, a, c, f: k)
#     def match(
#         self, call: T, reduce: T, accumulate: T, reduceat: T, outer: T, at: T
#     ) -> T:
#         ...


# class ArrayOrder(Expression):
#     @property  # type: ignore
#     @staticmethod
#     @expression
#     def k() -> ArrayOrder:
#         ...

#     @property  # type: ignore
#     @staticmethod
#     @expression
#     def a() -> ArrayOrder:
#         ...

#     @property  # type: ignore
#     @staticmethod
#     @expression
#     def c() -> ArrayOrder:
#         ...

#     @property  # type: ignore
#     @staticmethod
#     @expression
#     def f() -> ArrayOrder:
#         ...


# @expression
# def array(
#     object: NDArray,
#     dtype: Optional[DType],
#     copy: Boolean,
#     order: Optional[ArrayOrder],
#     subok: Optional[Boolean],
#     ndmin: Optional[Integer],
# ) -> NDArray:
#     ...


@expression
def arange(
    start: Optional[Number],
    stop: Number,
    step: Optional[Number],
    dtype: Optional[DType],
) -> NDArray:
    ...



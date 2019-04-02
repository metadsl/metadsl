from metadsl.expressions import *
from metadsl.python.pure import *
import typing

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
T = typing.TypeVar("T", bound=Instance)
U = typing.TypeVar("U", bound=Instance)


class NDArray(Instance):
    @property  # type: ignore
    @call(lambda self: instance_type(TupleOfIntegers))
    def shape(self) -> TupleOfIntegers:
        ...

    @call(lambda self, other: instance_type(NDArray))
    def __add__(self, other: "NDArray") -> "NDArray":
        ...

    @call(lambda self, other: instance_type(NDArray))
    def __mul__(self, other: "NDArray") -> "NDArray":
        ...

    @staticmethod
    @call(lambda *args: instance_type(NDArray))
    def __array_ufunc__(
        ufunc: "UFunc", method: "UFuncMethod", kwargs: "UFuncKwargs", *inputs: "NDArray",
    ) -> "NDArray":
        ...


class DType(Instance):
    pass


class UFunc(Instance):
    pass


class UFuncKwargs(Instance):
    pass


class UFuncMethod(Instance):
    """
    https://docs.scipy.org/doc/numpy-1.13.0/neps/ufunc-overrides.html#proposed-interface

    method is a string indicating how the Ufunc was called, either "__call__" to indicate it was called directly, or one of its methods: "reduce", "accumulate", "reduceat", "outer", or "at".
    """

    @call(lambda self, k, a, c, f: k)
    def match(
        self, call: T, reduce: T, accumulate: T, reduceat: T, outer: T, at: T
    ) -> T:
        ...


class ArrayOrder(Instance):
    @call(lambda self, k, a, c, f: k)
    def match(self, k: T, a: T, c: T, f: T) -> T:
        ...

    @property  # type: ignore
    @call(lambda: instance_type(ArrayOrder))
    @staticmethod
    def k() -> "ArrayOrder":
        ...

    @property  # type: ignore
    @call(lambda: instance_type(ArrayOrder))
    @staticmethod
    def a() -> "ArrayOrder":
        ...

    @property  # type: ignore
    @call(lambda: instance_type(ArrayOrder))
    @staticmethod
    def c() -> "ArrayOrder":
        ...

    @property  # type: ignore
    @call(lambda: instance_type(ArrayOrder))
    @staticmethod
    def f() -> "ArrayOrder":
        ...


@call(lambda object, dtype, copy, order, subok, ndmin: instance_type(NDArray))
def array(
    object: NDArray,
    dtype: Optional[DType],
    copy: Boolean,
    order: Optional[ArrayOrder],
    subok: Optional[Boolean],
    ndmin: Optional[Integer],
) -> NDArray:
    ...


@call(lambda start, stop, step, dtype: instance_type(NDArray))
def arange(
    start: Optional[Number],
    stop: Number,
    step: Optional[Number],
    dtype: Optional[DType],
) -> NDArray:
    ...

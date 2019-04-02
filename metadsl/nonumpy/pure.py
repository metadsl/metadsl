from metadsl.expressions import *
from metadsl.python.pure import *
import typing

__all__ = ["NDArray", "DType", "ArrayOrder", "Optional", "Number", "array", "arange"]
T = typing.TypeVar("T", bound=Instance)
U = typing.TypeVar("U", bound=Instance)


class NDArray(Instance):
    @property  # type: ignore
    @call(lambda self: instance_type(TupleOfIntegers))
    def shape(self) -> TupleOfIntegers:
        ...


class DType(Instance):
    pass


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

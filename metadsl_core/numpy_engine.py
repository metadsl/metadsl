import typing

import numpy
from metadsl import *

from . import numpy as numpy_api
from .abstraction import *
from .conversion import *
from .either import *
from .integer import *
from .maybe import *
from .pair import *
from .rules import *
from .vec import *

__all__ = ["ndarray_getitem"]

T = typing.TypeVar("T")


@expression
def unbox_integer(i: Integer) -> int:
    ...


@register_unbox  # type: ignore
@rule
def unbox_integer_rule(i: int) -> R[int]:
    return unbox_integer(Integer.from_int(i)), i


@expression
def arange(stop: int) -> numpy.ndarray:
    return numpy.arange(stop)


register_numpy_engine(default_rule(arange))


@register_unbox
@rule
def unbox_arange(i: Integer) -> R[numpy.ndarray]:
    return (numpy_api.arange_(i).to_ndarray(), arange(unbox_integer(i)))


@expression
def ndarray_getitem(
    self: numpy.ndarray, i: typing.Union[int, typing.Tuple[int, ...]]
) -> numpy.ndarray:
    # Always return array not scalars
    return numpy.array(self[i], ndmin=0)


register_numpy_engine(default_rule(ndarray_getitem))


@expression
def ndarray_add(self: numpy.ndarray, other: numpy.ndarray) -> numpy.ndarray:
    return self + other


register_numpy_engine(default_rule(ndarray_add))


@register_unbox  # type: ignore
@rule
def unbox_ndarray_add(a: numpy_api.NDArray, b: numpy_api.NDArray) -> R[numpy.ndarray]:
    return (a + b).to_ndarray(), ndarray_add(a.to_ndarray(), b.to_ndarray())


@expression
def unbox_idxs(
    idxs: Either[Integer, Vec[Integer]]
) -> typing.Union[int, typing.Tuple[int, ...]]:
    ...


@expression
def homo_tuple(*values: T) -> typing.Tuple[T, ...]:
    return tuple(values)


register(default_rule(homo_tuple))


@register_unbox  # type: ignore
@rule
def unbox_idxs_rule(
    i: Integer, ints: typing.Sequence[Integer]
) -> R[typing.Union[int, typing.Tuple[int, ...]]]:
    yield (unbox_idxs(Either[Integer, Vec[Integer]].left(i)), unbox_integer(i))
    yield (
        unbox_idxs(Either[Integer, Vec[Integer]].right(Vec.create(*ints))),
        lambda: homo_tuple(*(unbox_integer(i_) for i_ in ints)),  # type: ignore
    )


@register_unbox  # type: ignore
@rule
def unbox_ndarray_getitem(
    a: numpy_api.NDArray, idx: Either[Integer, Vec[Integer]]
) -> R[numpy.ndarray]:
    return a[idx].to_ndarray(), ndarray_getitem(a.to_ndarray(), unbox_idxs(idx))


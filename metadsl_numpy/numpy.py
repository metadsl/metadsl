# from __future__ import annotations

# import numpy
# from metadsl import *


# # TODO: Move to seperate numpy repo
# # inherit from ndarray like
# # but use "compat" types for shape etc.
# # Each should have a `to_xxx` method.
# from .vec import *
# from .integer import *
# from .conversion import *
# from .strategies import *
# from .maybe import *
# from .abstraction import *
# from .pair import *
# from .either import *


# __all__ = ["arange", "IndxType", "NDArray"]


# IndxType = Either[Integer, Vec[Integer]]


# class NDArray(Expression):
#     @expression
#     def __getitem__(self, idxs: IndxType) -> NDArray:
#         ...

#     @expression
#     def __add__(self, other: NDArray) -> NDArray:
#         ...

#     @expression
#     def to_ndarray(self) -> numpy.ndarray:
#         ...

#     @expression
#     @classmethod
#     def from_ndarray(cls, n: numpy.ndarray) -> NDArray:
#         ...

#     @expression
#     @classmethod
#     def from_ndarray(cls, n: numpy.ndarray) -> NDArray:
#         ...

# @register_unbox
# @rule
# def box_unbox_ndarray(n: numpy.ndarray) -> R[numpy.ndarray]:
#     return NDArray.from_ndarray(n).to_ndarray(), n


# class NDArrayCompat(Expression):
#     @expression
#     def __getitem__(self, idxs: object) -> NDArrayCompat:
#         return NDArrayCompat.from_ndarray(
#             (
#                 Converter[NDArray].convert(self)
#                 & Converter[Either[Integer, Vec[Integer]]].convert(idxs)
#             ).map(
#                 Abstraction[
#                     Pair[NDArray, Either[Integer, Vec[Integer]]], NDArray
#                 ].from_fn(lambda p: p.left[p.right])
#             )
#         )

#     @expression
#     def __add__(self, other: NDArrayCompat) -> NDArrayCompat:
#         ...

#     @expression
#     @classmethod
#     def from_ndarray(cls, n: Maybe[NDArray]) -> NDArrayCompat:
#         ...

#     @expression
#     def to_ndarray(self) -> numpy.ndarray:
#         ...


# def ndarray_getitem()

# @register_core
# @rule



# @register_unbox
# @rule
# def box_unbox_ndarray_compat(n: NDArray) -> R[numpy.ndarray]:
#     return (NDArrayCompat.from_ndarray(Maybe.just(n)).to_ndarray(), n.to_ndarray())


# @register_convert
# @rule
# def add_compat(l: NDArray, r: NDArray) -> R[NDArrayCompat]:
#     return (
#         NDArrayCompat.from_ndarray(Maybe.just(l))
#         + NDArrayCompat.from_ndarray(Maybe.just(r)),
#         NDArrayCompat.from_ndarray(Maybe.just(l + r)),
#     )


# register_convert(default_rule(NDArrayCompat.__getitem__))


# @register_convert
# @rule
# def convert_to_ndarray(i: Maybe[NDArray]) -> R[Maybe[NDArray]]:
#     return Converter[NDArray].convert(NDArrayCompat.from_ndarray(i)), i


# @expression
# def arange(stop: object) -> NDArrayCompat:
#     return NDArrayCompat.from_ndarray(
#         Converter[Integer].convert(stop).map(Abstraction.from_fn(arange_))
#     )


# register_convert(default_rule(arange))


# @expression
# def arange_(stop: Integer) -> NDArray:
#     ...

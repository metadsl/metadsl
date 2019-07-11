# from __future__ import annotations

# import typing

# from metadsl import *
# import metadsl.numpy.expressions as np
# import metadsl.python.wraps as py_wraps

# __all__ = ["arange", "NDArray"]

# T = typing.TypeVar("T")


# @wrap(np.arange)
# def arange(start, stop, step, dtype) -> NDArray:
#     ...


# class NDArray(Wrap[np.NDArray]):
#     @wrap(np.NDArray.shape)
#     def shape(self) -> py_wraps.IntegerTuple:
#         ...

#     @wrap(np.NDArray.__add__)
#     def __add__(self, other: object) -> NDArray:
#         ...

#     @wrap(np.NDArray.__mul__)
#     def __mul__(self, other: object) -> NDArray:
#         ...

#     @wrap(np.NDArray.__getitem__)
#     def __getitem__(self, idxs: object) -> NDArray:
#         ...
